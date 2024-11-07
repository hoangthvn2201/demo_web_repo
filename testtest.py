# 1. Model and Tokenizer Setup
model_path = 'phamhai/Llama-3.2-1B-Instruct-Frog'
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Load the model and move it to CUDA
model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")

# 2. Pipeline Configuration
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    do_sample=True,
    temperature=0.7,
    top_p=0.95,
    device=0  # Use GPU
)

# 3. Chatbot Class
class ContextAwareChatbot:
    def __init__(self, pipeline, max_history: int = 5):
        self.pipeline = pipeline
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.max_history = max_history
        self.conversation_history: List[Dict[str, str]] = []
        
    def _build_prompt(self) -> str:
        # Build context from history
        history_text = ""
        for exchange in self.conversation_history[-self.max_history:]:
            history_text += f"Human: {exchange['human']}\nAssistant: {exchange['assistant']}\n\n"
        
        # Create the full prompt with context
        prompt = f"""Bạn là một trợ lí ảo thông minh có thể trả lời những câu hỏi của người dùng. Dựa vào đoạn hội thoại trong quá khứ, cố gắng trả lời câu hỏi người dùng một cách chính xác và trung thực nhất.
Đoạn chat trong quá khứ:     
<START_OF_HISTORY_CONTEXT>
{history_text}
<END_OF_HISTORY_CONTEXT>"""
        return prompt
    
    def _clean_response(self, response: str) -> str:
        # Clean up the generated response
        response = response.split("Assistant:")[-1].strip()
        # Stop at any new "Human:" or "Assistant:" markers
        if "Human:" in response:
            response = response.split("Human:")[0].strip()
        return response
    
    def chat(self, user_input: str) -> str:
        # Generate the contextualized prompt
        prompt = self._build_prompt()
        
        # Create the chat messages with roles
        messages = [
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': user_input}
        ]

        # Tokenize input and ensure it is moved to the GPU
        tokenized_chat = self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors='pt').to("cuda")
        
        # Generate response
        outputs = self.model.generate(tokenized_chat['input_ids'], max_new_tokens=256)
        bot_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the assistant response
        bot_response = bot_response.split('<|start_header_id|>assistant<|end_header_id|>')[1].strip()[:-10]
        
        # Update conversation history
        self.conversation_history.append({
            'human': user_input,
            'assistant': bot_response
        })
        
        return bot_response
    
    def get_history(self) -> List[Dict[str, str]]:
        return self.conversation_history
    
    def clear_history(self):
        self.conversation_history = []

# 4. Create chatbot instance
chatbot = ContextAwareChatbot(pipe)
