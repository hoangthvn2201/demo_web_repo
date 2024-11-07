from transformers import AutoModelForCausalLM, AutoTokenizer
import mysql.connector as connection
import utils 
import pandas as pd 

model_path = "phamhai/Llama-3.2-1B-Instruct-Frog"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)


mydb = connection.connect(host="127.0.0.1", database = 'db2',user="root", passwd="2787853")
cursor = mydb.cursor()
query = "Select * from jidouka;"
df = pd.read_sql(query,mydb)
df.rename(columns={'pic':'contributor'}, inplace=True)

chatbot_df = utils.format_table_for_chatbot(df)
prompt_template=""" Bạn là một trợ lí ảo thông minh
                    ###Nhiệm vụ: trả lời câu hỏi của người dùng dựa vào bảng cho dưới đây. Nếu câu hỏi không liên quan đến bảng, hãy bắt đầu bằng: "Tôi không thể tìm được dữ kiện trong bảng bạn cần tìm".
                    ###Bảng:
                    {table}
                """
system_prompt = prompt_template.format(table=chatbot_df)
messages = [
    {"role": "system", 
     "content": system_prompt}
    ,{"role": "user", "content":"Có bao nhiêu người tham gia đóng góp vào bảng, đó là những ai?"}
]

tokenized_chat = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors='pt')

outputs = model.generate(tokenized_chat, max_new_tokens=256)
print(tokenizer.decode(outputs[0]))