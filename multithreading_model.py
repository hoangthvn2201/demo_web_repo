from transformers import pipeline, MBartForConditionalGeneration, MBart50TokenizerFast
import mysql.connector as connection
import pandas as pd
import time
from utils import *
from sqlalchemy import create_engine
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

class MultilingualQABot:
    def __init__(self):
        self.tapas_pipe = None
        self.mbart_model = None
        self.mbart_tokenizer = None
        self.df = None
        self.model_loaded = threading.Event()
        self.data_loaded = threading.Event()
        
    def load_models(self):
        """Load ML models in a separate thread"""
        self.tapas_pipe = pipeline("table-question-answering", 
                                 model='google/tapas-large-finetuned-wtq')
        self.mbart_model = MBartForConditionalGeneration.from_pretrained(
            "facebook/mbart-large-50-many-to-many-mmt")
        self.mbart_tokenizer = MBart50TokenizerFast.from_pretrained(
            "facebook/mbart-large-50-many-to-many-mmt")
        self.model_loaded.set()

    def load_data(self):
        """Load database data in a separate thread"""
        engine = create_engine(
            "mysql+mysqlconnector://root:2787853@127.0.0.1:3306/db2",
            echo=False
        )
        cnx = engine.raw_connection()
        self.df = pd.read_sql('SELECT * FROM jidouka', cnx)
        self.df = self.df.astype(str)
        self.df.rename(columns={'pic': 'contributor'}, inplace=True)
        cnx.close()
        self.data_loaded.set()

    def translate_text(self, text_vi):
        """Translate Vietnamese text to English"""
        self.model_loaded.wait()  # Wait for models to be loaded
        
        self.mbart_tokenizer.src_lang = 'vi_VN'
        encoded_vi = self.mbart_tokenizer(text_vi, return_tensors='pt')
        generated_tokens = self.mbart_model.generate(
            **encoded_vi,
            forced_bos_token_id=self.mbart_tokenizer.lang_code_to_id['en_XX']
        )
        
        text = self.mbart_tokenizer.batch_decode(
            generated_tokens, 
            skip_special_tokens=True
        )[0]
        return text

    def answer_question(self, text):
        """Generate answer using TAPAS"""
        self.model_loaded.wait()  # Wait for models to be loaded
        self.data_loaded.wait()   # Wait for data to be loaded
        
        result = self.tapas_pipe(table=self.df, query=text)["answer"]
        return format_result_tapas(result)

    def process_query(self, text_vi):
        """Process a Vietnamese query end-to-end"""
        start = time.time()
        
        # Start loading models and data in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit background tasks
            model_future = executor.submit(self.load_models)
            data_future = executor.submit(self.load_data)
            
            # Wait for both to complete
            for future in as_completed([model_future, data_future]):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error during initialization: {e}")
                    return None

            # Translate and answer in sequence (they depend on the models/data)
            translation = self.translate_text(text_vi)
            final_answer = self.answer_question(translation)

        end = time.time()
        
        return final_answer
