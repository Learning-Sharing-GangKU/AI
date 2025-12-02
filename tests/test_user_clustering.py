# tests/test_user_clustering.py
# python -m pytest -q tests/test_user_clustering.py

"""
사용자 군집화 로직(ClusteringTrainer)의 핵심 내부 함수들을 단위 테스트하는 모듈입니다.

테스트 대상:
- _build_numeric_matrix
- _build_multi_hot_matrix
- _fit_svd

이 세 함수는 군집화 성능과 직접적으로 연결되므로,
입출력이 의도대로 동작하는지 반드시 검증해 두는 것이 좋습니다.
"""

from typing import List

import numpy as np
import pytest

from app.cluster.user_clustering import ClusteringTrainer
from app.models.schemas import RecommendByClusteringModelRequest
from app.models.enums import Category


def _make_user(
    *,
    user_age: int | None,
    user_enroll: int | None,
    user_join_count: int | None,
    preferred_categories: List[Category],
) -> RecommendByClusteringModelRequest:
    """
    테스트에서 사용할 RecommendByClusteringModelRequest 인스턴스를 생성하는 유틸 함수입니다.

    실제 스키마에 필드가 더 있다면, 이 함수의 인자에 추가로 받아서
    RecommendByClusteringModelRequest(...) 에 함께 넘겨주시면 됩니다.
    """
    return RecommendByClusteringModelRequest(
        age=user_age,
        enrollNumber=user_enroll,
        user_join_count=user_join_count,
        preferredCategories=preferred_categories,
    )


@pytest.fixture
def trainer() -> ClusteringTrainer:
    """
    ClusteringTrainer 인스턴스를 생성하는 pytest fixture 입니다.

    - artifacts_dir는 테스트에서 직접 사용하지 않으므로 None으로 두어,
      기본 경로(app/cluster/artifacts 또는 현재 구현에서 정한 기본 경로)를 사용하게 합니다.
    """
    return ClusteringTrainer(artifacts_dir=None)


@pytest.fixture
def sample_users() -> List[RecommendByClusteringModelRequest]:
    """
    multi-hot, numeric 행렬 테스트에 사용할 샘플 사용자 3명을 생성합니다.

    설정:
    - user 0:
        age = 20
        enroll = 2022
        join_count = 3
        preferred_categories = ["음악", "게임"]
    - user 1:
        age = 22
        enroll = 2021
        join_count = 5
        preferred_categories = ["게임"]
    - user 2:
        age = None        → numeric 행렬에서 0으로 채워져야 함
        enroll = None     → numeric 행렬에서 0으로 채워져야 함
        join_count = None → numeric 행렬에서 0으로 채워져야 함
        preferred_categories = ["스터디"]
    """
    u0 = _make_user(
        user_age=20,
        user_enroll=2022,
        user_join_count=3,
        preferred_categories=[Category("음악"), Category("게임")],
    )
    u1 = _make_user(
        user_age=22,
        user_enroll=2021,
        user_join_count=5,
        preferred_categories=[Category("게임")],
    )
    u2 = _make_user(
        user_age=None,
        user_enroll=None,
        user_join_count=None,
        preferred_categories=[Category("스터디")],
    )
    return [u0, u1, u2]


def test_build_numeric_matrix_basic(
    trainer: ClusteringTrainer,
    sample_users: List[RecommendByClusteringModelRequest],
) -> None:
    """
    _build_numeric_matrix가 user_age, user_enroll, user_join_count를
    올바른 순서와 값으로 numpy 배열에 채우는지 검증합니다.

    기대사항:
    - 반환되는 행렬의 shape는 (n_users, 3) 이어야 합니다.
      (열 순서: [user_age, user_enroll, user_join_count])
    - None 값은 0으로 대체되어야 합니다.
    """
    mat = trainer._build_numeric_matrix(sample_users)

    # 1) 전체 shape 검증
    assert mat.shape == (3, 3)

    # 2) 각 사용자별 값 검증
    # user 0
    assert mat[0, 0] == 20
    assert mat[0, 1] == 2022
    assert mat[0, 2] == 3

    # user 1
    assert mat[1, 0] == 22
    assert mat[1, 1] == 2021
    assert mat[1, 2] == 5

    # user 2: None 값들은 모두 0으로 치환되어야 함
    assert mat[2, 0] == 0
    assert mat[2, 1] == 0
    assert mat[2, 2] == 0


def test_build_multi_hot_matrix_basic(
    trainer: ClusteringTrainer,
    sample_users: List[RecommendByClusteringModelRequest],
) -> None:
    """
    _build_multi_hot_matrix가 주어진 vocab과 사용자 선호 카테고리 정보를 기반으로
    올바른 multi-hot 행렬을 생성하는지 검증합니다.

    테스트 설정:
    - vocab: ["스터디", "게임", "음악"] 으로 고정 (정렬된 상태라고 가정)
      (실제 _build_category_vocab를 쓰면 "스터디", "게임", "음악" 순으로 나올 수 있습니다.)
    - user 0: ["음악", "게임"] → [0, 1, 1]
    - user 1: ["게임"]        → [0, 1, 0]
    - user 2: ["스터디"]        → [1, 0, 0]
    """
    vocab = ["스터디", "게임", "음악"]
    mat = trainer._build_multi_hot_matrix(sample_users, vocab)

    # 1) 전체 shape 검증: (3명, 3카테고리)
    assert mat.shape == (3, 3)

    # 2) 각 행이 예상되는 multi-hot 벡터와 일치하는지 검증
    np.testing.assert_array_equal(
        mat[0],
        np.array([0.0, 1.0, 1.0], dtype=np.float32),
    )
    np.testing.assert_array_equal(
        mat[1],
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
    )
    np.testing.assert_array_equal(
        mat[2],
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
    )


def test_fit_svd_reduces_dimension(
    trainer: ClusteringTrainer,
    sample_users: List[RecommendByClusteringModelRequest],
) -> None:
    """
    _fit_svd가 multi-hot 행렬을 받아,
    지정된 n_components 이하의 차원으로 잘 축소하는지 검증합니다.

    설정:
    - vocab: ["스터디", "게임", "음악"] → n_cats = 3
    - n_components 요청값: 2
    기대:
    - 실제 사용된 n_components_eff = min(요청값, n_cats, n_users) = 2
    - 반환된 features의 shape는 (n_users, 2) 이어야 합니다.
    """
    vocab = ["스터디", "게임", "음악"]
    multi_hot = trainer._build_multi_hot_matrix(sample_users, vocab)

    svd, features = trainer._fit_svd(multi_hot, n_components=2)

    # 1) SVD가 요청대로 2차원으로 축소했는지 검증
    assert svd.n_components == 2

    # 2) 반환된 feature 행렬의 shape 검증
    assert features.shape == (3, 2)


def test_fit_svd_when_no_categories(trainer: ClusteringTrainer) -> None:
    """
    _fit_svd가 '카테고리가 전혀 없는 경우(n_cats == 0)'에도
    안전하게 동작하는지 검증합니다.

    설정:
    - multi_hot: shape = (3, 0) 즉, 사용자 3명인데 카테고리 열이 0개
    기대:
    - 내부에서 n_components_eff가 최소 1로 보정되어,
      svd.n_components == 1 이어야 합니다.
    - 반환되는 features의 shape는 (3, 1) 이고, 모든 값은 0이어야 합니다.
    """
    n_users = 3
    # 열이 0개인 multi-hot 행렬 생성
    multi_hot = np.zeros((n_users, 0), dtype=np.float32)

    svd, features = trainer._fit_svd(multi_hot, n_components=4)

    # 1) SVD 컴포넌트 수가 1로 보정되었는지 검증
    assert svd.n_components == 1

    # 2) feature 행렬 shape 검증
    assert features.shape == (n_users, 1)
    print(features)

    # 3) 모든 값이 0인지 검증
    assert np.allclose(features, 0.0)
