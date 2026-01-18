from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class PhiGenerator:
    def __init__(self, model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        self.device = "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True
        ).to(self.device)
        self.model.eval()

    def generate(self, prompt, max_new_tokens=250):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.1,
                top_k=50,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )

        response = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        return response.strip()

    def get_prompt_template(self, mode, query, context):
        system_msg = "You are StudySource AI, a helpful study assistant. Answer questions ONLY based on the provided context. If the answer is not in the context, say 'Not in uploaded sources'. Do not use external knowledge."

        if mode == "simple":
            user_msg = f"Context: {context}\n\nQuestion: {query}\n\nInstructions: Explain like I'm 12. Use simple words. Max 5 sentences. No metaphors. Answer based ONLY on the context."
        elif mode == "summary":
            user_msg = f"Context: {context}\n\nTask: Provide a bulleted summary of the context above. Use 5-7 points. Content-faithful only."
        else: # Normal
            user_msg = f"Context: {context}\n\nQuestion: {query}\n\nInstructions: Provide a clear explanation based ONLY on the context above. If not found, say 'Not in uploaded sources'."

        return f"<|system|>\n{system_msg}</s>\n<|user|>\n{user_msg}</s>\n<|assistant|>\n"

    def generate_grounded_answer(self, mode, query, retrieved_results):
        if not retrieved_results:
            return "Not in uploaded sources."

        context = "\n---\n".join([r["chunk"]["text"] for r in retrieved_results])
        prompt = self.get_prompt_template(mode, query, context)

        return self.generate(prompt)
