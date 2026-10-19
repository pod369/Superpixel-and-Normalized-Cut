"""Compare SLIC compactness and merge superpixels with normalized cut."""

import argparse
import inspect
import json
from pathlib import Path
import time

import cv2 as cv
import numpy as np
import skimage
from skimage import color, data, graph, segmentation


PROJECT_DIR = Path(__file__).resolve().parent


def recorded_path(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_DIR).as_posix()
    except ValueError:
        return str(resolved)


def write_rgb(path, image):
    if image.dtype != np.uint8:
        image = np.clip(np.rint(image * 255), 0, 255).astype(np.uint8)
    if not cv.imwrite(str(path), cv.cvtColor(image, cv.COLOR_RGB2BGR)):
        raise OSError(f"Could not save image: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, help="Custom image; default is the bundled skimage coffee sample.")
    parser.add_argument("--max-side", type=int, default=320, help="Downsample longest side; 0 keeps original resolution.")
    parser.add_argument("--segments", type=int, default=200, help="Requested SLIC segments; actual count may differ.")
    parser.add_argument("--sigma", type=float, default=255.0, help="Similarity RAG sigma used in exp(-color_distance^2 / sigma).")
    parser.add_argument("--cut-threshold", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_DIR / "outputs")
    parser.add_argument("--show", action="store_true", help="Display results with a GUI-enabled OpenCV build.")
    args = parser.parse_args()
    if args.max_side < 0 or args.segments < 2 or args.sigma <= 0 or args.cut_threshold <= 0:
        parser.error("--max-side must be nonnegative, --segments at least 2, and sigma/cut-threshold positive.")
    if args.image:
        loaded = cv.imread(str(args.image), cv.IMREAD_COLOR)
        if loaded is None:
            parser.error(f"Could not read image: {args.image}")
        image = cv.cvtColor(loaded, cv.COLOR_BGR2RGB)
        input_name = recorded_path(args.image)
    else:
        image = data.coffee()
        input_name = "skimage.data.coffee()"
    original_shape = list(image.shape)
    if args.max_side and max(image.shape[:2]) > args.max_side:
        scale = args.max_side / max(image.shape[:2])
        image = cv.resize(image, (max(1, round(image.shape[1] * scale)), max(1, round(image.shape[0] * scale))),
                          interpolation=cv.INTER_AREA)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = {"input.png": image}
    metrics = {
        "input": input_name, "original_shape_hwc": original_shape, "processed_shape_hwc": list(image.shape),
        "max_side": args.max_side, "requested_segments": args.segments,
        "rag_sigma": args.sigma, "cut_threshold": args.cut_threshold, "seed": args.seed,
        "scikit_image_version": skimage.__version__, "status": "completed", "slic": {},
    }
    slic_labels = {}
    for compactness in (20, 40):
        started = time.perf_counter()
        labels = segmentation.slic(image, n_segments=args.segments, compactness=compactness,
                                   start_label=1, channel_axis=-1)
        slic_labels[compactness] = labels
        metrics["slic"][str(compactness)] = {"compactness": compactness,
                                             "actual_segments": int(np.unique(labels).size),
                                             "seconds": time.perf_counter() - started}
        results[f"slic_compactness_{compactness}.png"] = segmentation.mark_boundaries(image, labels)
        np.save(args.output_dir / f"slic_labels_{compactness}.npy", labels)
    started = time.perf_counter()
    labels = slic_labels[20]
    rag = graph.rag_mean_color(image, labels, mode="similarity", sigma=args.sigma)
    cut_options = {"thresh": args.cut_threshold}
    # scikit-image renamed random_state to rng. Support both released interfaces.
    parameters = inspect.signature(graph.cut_normalized).parameters
    if "rng" in parameters:
        cut_options["rng"] = args.seed
    elif "random_state" in parameters:
        cut_options["random_state"] = args.seed
    try:
        merged = graph.cut_normalized(labels, rag, **cut_options)
        metrics["normalized_cut"] = {"segments": int(np.unique(merged).size),
                                      "seconds": time.perf_counter() - started,
                                      "source_compactness": 20}
        results["normalized_cut_boundaries.png"] = segmentation.mark_boundaries(image, merged)
        results["normalized_cut_mean_color.png"] = color.label2rgb(merged, image / 255.0, kind="avg", bg_label=-1)
        np.save(args.output_dir / "normalized_cut_labels.npy", merged)
    except (ValueError, RuntimeError, TypeError) as exc:
        metrics["status"] = "normalized_cut_failed"
        metrics["normalized_cut"] = {"seconds": time.perf_counter() - started, "error": str(exc)}
    for name, result in results.items():
        write_rgb(args.output_dir / name, result)
    (args.output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Saved results to {args.output_dir.resolve()}")
    if args.show:
        for name, result in results.items():
            display = np.clip(np.rint(result * 255), 0, 255).astype(np.uint8) if result.dtype != np.uint8 else result
            cv.imshow(name, cv.cvtColor(display, cv.COLOR_RGB2BGR))
        cv.waitKey(0)
        cv.destroyAllWindows()
    return 0 if metrics["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
