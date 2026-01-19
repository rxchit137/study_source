from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class PhiGenerator:
    def __init__(self, model_id="gpt2"):
        self.device = "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        # GPT2 doesn't have a pad token by default
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        base_model = AutoModelForCausalLM.from_pretrained(
            model_id,
            low_cpu_mem_usage=True
        )

        # Apply dynamic quantization for int8
        self.model = torch.quantization.quantize_dynamic(
            base_model, {torch.nn.Linear}, dtype=torch.qint8
        ).to(self.device)
        self.model.eval()

    def generate(self, prompt, max_new_tokens=150):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id
            )

        response = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        return response.strip()

    def get_prompt_template(self, mode, query, context):
        # GPT-2 is a base model, so we use a clear instructional prompt structure
        if mode == "simple":
            return f"The following is a study guide context:\n{context}\n\nQuestion: {query}\nInstruction: Explain the answer simply for a 12-year old student using at most 5 sentences. Only use the context provided.\nAnswer:"
        elif mode == "summary":
            return f"The following is a study guide context:\n{context}\n\nInstruction: Provide a short bulleted summary of the context using 5-7 points.\nSummary:"
        else: # Normal
            return f"The following is a study guide context:\n{context}\n\nQuestion: {query}\nInstruction: Provide a clear explanation based only on the context above. If the information is not present, say 'Not in uploaded sources'.\nAnswer:"

    def generate_grounded_answer(self, mode, query, retrieved_results):
        if not retrieved_results:
            return "Not in uploaded sources."

        context = "\n---\n".join([r["chunk"]["text"] for r in retrieved_results])
        prompt = self.get_prompt_template(mode, query, context)

        return self.generate(prompt)
