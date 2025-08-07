import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from langchain_community.llms import HuggingFacePipeline
from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain.prompts import PromptTemplate
from transformers import pipeline
from langchain.chains import LLMChain

from generator import Phi15Generator
from retriever import retrieve_top_k


E5_MODEL_PATH = r"C:\PythonEnvs\huggingface\OPIc_Buddy\model\models--intfloat--e5-base-v2\snapshots\f52bf8ec8c7124536f0efb74aca902b2995e5bcd"
PHI15_MODEL_PATH = r"C:\PythonEnvs\huggingface\OPIc_Buddy\model\models--microsoft--phi-1_5\snapshots\675aa382d814580b22651a30acb1a585d7c25963"

MONGO_URI = "mongodb+srv://hakliml22:Lifegoeson%211@cluster0.1ryjiuy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "OPIcBuddy"
COLLECTION_NAME = "embedded_opic_samples"

# 환경 설정
# E5_MODEL_PATH    = os.getenv("E5_MODEL_PATH")
# PHI15_MODEL_PATH = os.getenv("PHI15_MODEL_PATH")
# MONGO_URI        = os.getenv("MONGO_URI")
# DB_NAME          = os.getenv("DB_NAME", "OPIcBuddy")
# COLLECTION_NAME  = os.getenv("COLLECTION_NAME", "embedded_opic_samples")

# Generator
hf_pipe = pipeline(
    "text-generation",
    model=os.getenv("PHI15_MODEL_PATH"),
    tokenizer=os.getenv("PHI15_MODEL_PATH"),
    device=0,  # GPU가 있으면 0, 없으면 -1
    temperature=0.2
)
llm = HuggingFacePipeline(pipeline=hf_pipe)

# Prompt 템플릿 정의
prompt_template = """
### [INST]
Instruction: Answer the question based on your knowledge.
Here is context to help:

{context}

### QUESTION:
{question}

[/INST]
"""
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=prompt_template
)


chain = LLMChain(llm=llm, prompt=prompt)


def run_rag(question: str, k: int = 3) -> str:
    # 2-1) retrieve_top_k 으로 가장 유사한 k개 문장 가져오기
    contexts = retrieve_top_k(question, k)

    # 2-2) 리스트를 하나의 문자열로 결합
    merged_context = "\n".join(contexts)

    # 2-3) LLMChain에 넘겨서 답변 생성
    return chain.run(context=merged_context, question=question)