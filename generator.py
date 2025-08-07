# model/generator.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

class Phi15Generator:
    def __init__(self, model_path: str, max_new_tokens: int = 40):
        self.device         = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer      = AutoTokenizer.from_pretrained(model_path)
        self.model          = AutoModelForCausalLM.from_pretrained(model_path).to(self.device)
        self.model.eval()
        self.max_new_tokens = max_new_tokens

    def generate(self, prompt: str) -> str:
        inputs  = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)