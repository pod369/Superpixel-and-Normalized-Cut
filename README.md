# Superpixel and Normalized Cut

이번 실행에서 320×213 coffee 영상의 SLIC 영역은 compactness 20/40에서 각각 204/216개였고, Normalized Cut으로 병합한 결과는 21개 영역이었습니다. 실제 결과와 설정은 `results/metrics.json`에 있습니다.

![실제 Normalized Cut 분할 결과](results/normalized_cut_mean_color.png)

**포트폴리오 제목: SLIC 및 Normalized Cut 기반 영상 분할**

SLIC로 이미지를 작은 영역인 슈퍼픽셀로 나눈 후, 영역 인접 그래프(RAG)를 만들고 Normalized Cut으로 유사한 영역을 병합합니다. SLIC의 `compactness=20`과 `40`을 비교하고, `20`의 결과를 그래프 분할 입력으로 사용합니다.

## 처리 과정과 설정

- 기본 이미지: scikit-image에 포함된 `skimage.data.coffee()`.
- SLIC: 요청 영역 수 200개, compactness 20/40, `start_label=1`.
- 기본 크기: 긴 변을 최대 320픽셀로 축소합니다. 실제 처리 크기를 JSON에 기록합니다.
- 그래프: 평균 색상을 이용한 인접 그래프, `mode="similarity"`, `sigma=255.0`.
- Normalized Cut: 기본 분할 임계값 `0.001`, 난수 시드 `0`.

`n_segments`는 요청값이므로 실제 생성된 영역 수와 다를 수 있습니다. compactness가 커지면 색상 유사도에 비해 공간적 규칙성을 더 강조합니다. Normalized Cut 결과는 의미 있는 객체 클래스가 아니라 색상과 인접 관계에 따른 영역입니다.

## 실행

Python 3.10 이상을 권장합니다. 아래 명령은 **저장소 루트**에서 실행합니다.

```bash
python -m pip install -r requirements.txt
python superpixel_and_normalized_cut.py
```

원본과 같은 전체 해상도·요청 영역 600개 설정으로 실행할 수도 있습니다. 기본 설정보다 시간이 더 걸릴 수 있습니다.

```bash
python superpixel_and_normalized_cut.py --max-side 0 --segments 600 --output-dir results/segmentation_full
python superpixel_and_normalized_cut.py --image results/input.png --max-side 320 --segments 150 --output-dir results/segmentation_custom
```

기본 출력은 `outputs/`입니다. 기본 경로는 작업 폴더와 독립적입니다. 사용자 지정 상대 경로는 명령 실행 위치를 기준으로 해석합니다. `--show`를 추가하면 결과 창을 표시하며, GUI 환경과 GUI를 지원하는 OpenCV가 필요합니다.

## 생성 자료

| 파일 | 내용 |
|---|---|
| `input.png` | 실제 분할에 사용한 이미지 |
| `slic_compactness_20.png`, `slic_compactness_40.png` | SLIC 영역 경계 비교 |
| `normalized_cut_boundaries.png` | 병합한 영역의 경계 |
| `normalized_cut_mean_color.png` | 병합 영역을 각 영역의 평균 색으로 표시 |
| `slic_labels_20.npy`, `slic_labels_40.npy` | SLIC 정수 영역 라벨 배열 |
| `normalized_cut_labels.npy` | Normalized Cut 정수 라벨 배열 |
| `metrics.json` | 입력·처리 크기, 요청·실제 영역 수, 파라미터, 시간, 버전, 처리 상태 |

`metrics.json`의 `status`가 `completed`인지 확인합니다. 그래프 분할에 실패하면 SLIC 결과와 오류 정보를 저장하고 종료 코드 1을 반환합니다. 따라서 결과 이미지가 없는 단계는 성공한 실험으로 작성하면 안 됩니다.

## 원본과 보완 내용

원본 저장소: [pod369/Image-processing-4](https://github.com/pod369/Image-processing-4)

| 원본 | 기능 | 보관 위치 |
|---|---|---|
| `play_4_5.py` | compactness 20/40의 SLIC 비교 | `reference/play_4_5.py` |
| `play_4_6.py` | SLIC + 영역 인접 그래프 + Normalized Cut | `reference/play_4_6.py` |

두 실습을 하나로 통합했습니다. CLI 설정, 선택적 크기 축소, 이미지·라벨 배열·측정값 저장, 사용자 이미지 입력, 명시적 `skimage.graph` import를 추가했습니다. scikit-image의 `rng`/`random_state` 매개변수 차이를 확인하여 시드를 전달합니다. 기본 설정이 원본의 600개·전체 해상도와 다르다는 점을 명시했습니다. `reference/`에는 원본을 보존했습니다.

## 한계 및 추가 실험

Normalized Cut은 영역 그래프 크기와 이미지 내용에 따라 계산 비용이 커질 수 있습니다. 색상이 비슷한 다른 객체를 합치거나, 한 객체를 여러 영역으로 나눌 수 있습니다. 정답 분할 마스크가 없으므로 영역 수와 시각적 비교를 분할 정확도로 해석하지 않습니다. 동일 입력 크기에서 compactness·요청 영역 수·sigma를 하나씩 바꾸어 결과와 시간을 비교하는 실험을 추가할 수 있습니다.

## AI-Ex 포트폴리오

2026년 2학기 AI-Ex 포트폴리오의 개별 프로젝트입니다. 원본 파일은 `reference/`에 보존했으며, 정리한 실행 코드와 원본을 구분했습니다. 원본 기준 커밋은 `b2f9a5b94bbe353cce22ce469e358bb2715759ce`입니다. 원본 재배포 라이선스는 별도로 추가하지 않았습니다.

실행 예시와 결과 설명은 이 저장소의 루트 구조에 맞췄습니다. `results/`에 포함된 측정 기록은 2026-10-14 실행 당시의 자료로, 과거 통합 폴더 경로가 메타데이터에 남아 있을 수 있습니다.

| 관련 프로젝트 |
|---|
| [SIFT Matching and Homography](https://github.com/pod369/SIFT-Matching-and-Homography) |
| [Edge and Contour Detection](https://github.com/pod369/Edge-and-Contour-Detection) |
| [Image and Video Effects](https://github.com/pod369/Image-and-Video-Effects) |
| [MNIST Handwritten Digit Recognition](https://github.com/pod369/MNIST-Handwritten-Digit-Recognition) |
| [YOLO Hangul Text Detection](https://github.com/pod369/YOLO-Hangul-Text-Detection) |

개별 저장소 검증일: **2026-10-19**. `/tmp` 작업 폴더에서 기본 입력으로 실행해 결과 저장을 확인했습니다. 원본 코드와 입력 이미지의 SHA-256도 보존 여부를 확인했습니다. 기존 `results/`는 2026-10-14 실행 기록을 유지합니다.
