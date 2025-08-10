# quest.py
import random
from collections import defaultdict, deque
from typing import List, Optional, Dict
from retriever import retrieve_top_k

EMBED_MODEL_PATH = r"C:\PythonEnvs\huggingface\OPIc_Buddy\model\models--intfloat--e5-base-v2\snapshots\f52bf8ec8c7124536f0efb74aca902b2995e5bcd"

# ---------- 휴리스틱 카테고리 분류 ----------
def infer_category_heuristic(q: str) -> str:
    s = q.lower()
    # role-play 유형
    if "role play" in s or "role-play" in s or s.startswith("role play:") or s.startswith("role-play:"):
        return "role_play"
    if s.startswith("imagine ") or s.startswith("suppose ") or s.startswith("pretend ") or "i will act as" in s:
        return "role_play"
    # 랜덤/라이트한 질문 힌트
    rnd_kw = ["random", "fun", "surprising", "unexpected", "would you rather", "lightning round"]
    if any(k in s for k in rnd_kw):
        return "random_question"
    return "survey"

# ---------- 텍스트 전처리 ----------
def _split_dedup(lines_like: List[str]) -> List[str]:
    seen = set()
    out = []
    for ctx in lines_like:
        for line in str(ctx).splitlines():
            s = line.strip()
            if not s:
                continue
            if len(s) < 10:              # 너무 짧은 것 제외
                continue
            if s in seen:
                continue
            seen.add(s)
            out.append(s)
    return out

# ---------- survey 키 매칭 ----------
def _normalize_key(k: str) -> str:
    return k.lower().replace("_", " ").strip()

def infer_survey_key(question: str, survey_keys: List[str]) -> Optional[str]:
    """
    질문이 어떤 survey 키(토픽)에 가장 잘 맞는지 간단 매칭.
    - 기본: 키 문자열(언더바->공백) 포함 여부로 매칭
    - 여러 키가 매칭되면 가장 먼저 잡힌 키 반환
    """
    s = question.lower()
    for k in survey_keys:
        nk = _normalize_key(k)
        if nk and nk in s:
            return k
    return None  # 못 찾으면 None

def _pick_n(cands: List[str], n: int, rng: random.Random) -> List[str]:
    if not cands:
        return []
    if len(cands) <= n:
        rng.shuffle(cands)
        return cands
    return rng.sample(cands, n)

# ---------- 메인 함수 ----------
def sample_opic_test(
    user_input: str,
    survey_keys: List[str],                 # 네가 넘겨주는 15개 키
    k_retrieve: int = 400,                  # 넉넉히 가져와서 필터링
    seed: Optional[int] = 42,
    # retrieve_top_k 전달 옵션
    collection_name: str = "embedded_opic_samples",
    model_path: str = EMBED_MODEL_PATH,
    text_field: str = "content",
    emb_field: str = "embedding",
    category: Optional[str] = None,
    topic: Optional[str] = None,
    # 고정 자기소개 문항
    intro_question: str = "Please introduce yourself. Tell me your name, where you’re from, and a few things about your background."
) -> List[str]:
    """
    구성:
    1) 자기소개 1개 (항상 1번)
    2) survey 11개 (가능하면 서로 다른 survey_keys에서 다양하게 선발)
    3) role_play 1개
    4) random_question 2개
    총 15문항
    """
    rng = random.Random(seed)

    # 1) Retrieval
    contexts = retrieve_top_k(
        query=user_input,
        model_path=model_path,
        collection_name=collection_name,
        k=k_retrieve,
        text_field=text_field,
        emb_field=emb_field,
        category=category,
        topic=topic
    )  # -> List[str]

    # 2) 정리/중복제거
    questions = _split_dedup(contexts)

    # 3) 카테고리 분류
    buckets: Dict[str, List[str]] = defaultdict(list)
    for q in questions:
        buckets[infer_category_heuristic(q)].append(q)

    # 4) 자기소개 고정
    intro_q = intro_question.strip()
    picked: List[str] = [intro_q]

    # 5) survey 11개 선택 - survey_keys 다양성 보장
    survey_pool = [q for q in buckets.get("survey", []) if q != intro_q]

    # survey_pool을 키별 버킷으로 분류
    key2qs: Dict[str, List[str]] = defaultdict(list)
    misc_qs: List[str] = []  # 어떤 키에도 매칭 안된 survey
    for q in survey_pool:
        key = infer_survey_key(q, survey_keys)
        if key is None:
            misc_qs.append(q)
        else:
            key2qs[key].append(q)

    # 각 키 버킷 섞기
    for k in key2qs:
        rng.shuffle(key2qs[k])
    rng.shuffle(misc_qs)

    survey_needed = 11
    survey_picked: List[str] = []

    # 5-1) 가능하면 키를 겹치지 않게 한 바퀴씩(라운드 로빈)
    keys_order = list(survey_keys)
    rng.shuffle(keys_order)
    rr = deque(keys_order)

    while rr and len(survey_picked) < survey_needed:
        k = rr.popleft()
        bucket = key2qs.get(k, [])
        if bucket:
            survey_picked.append(bucket.pop())
        # 아직 해당 키에 남아있으면 다시 큐에 넣어 다음 라운드에 또 뽑을 기회 부여
        if bucket:
            rr.append(k)

        # 모든 키가 비어버리면 루프 탈출
        if not any(key2qs.get(kk, []) for kk in rr):
            break

    # 5-2) 아직 모자라면, 남은 키 버킷 + misc에서 채우기
    if len(survey_picked) < survey_needed:
        leftovers = []
        for k in survey_keys:
            leftovers.extend(key2qs.get(k, []))
        leftovers.extend(misc_qs)
        rng.shuffle(leftovers)
        need = survey_needed - len(survey_picked)
        survey_picked.extend(leftovers[:need])

    picked.extend(survey_picked[:survey_needed])

    # 6) role_play 1개
    picked.extend(_pick_n(buckets.get("role_play", []), 1, rng))

    # 7) random_question 2개
    picked.extend(_pick_n(buckets.get("random_question", []), 2, rng))

    # 8) 부족하면 전체에서 채우기(예외적 상황)
    need_total = 15
    if len(picked) < need_total:
        all_leftovers = [q for q in questions if q not in picked and q != intro_q]
        rng.shuffle(all_leftovers)
        picked.extend(all_leftovers[: need_total - len(picked)])

    # 9) 최종 길이/순서 보정 (자기소개 항상 1번)
    picked = picked[:need_total]
    if picked[0] != intro_q:
        if intro_q in picked:
            picked.remove(intro_q)
        picked.insert(0, intro_q)

    return picked
