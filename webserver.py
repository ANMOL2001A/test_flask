from flask import Flask
from datetime import datetime
#from logman import Logger
# from llm.storage.vector import BeckHealthVectorStore
# from _pathmaker import get_vector_storage_path


# logger_instance = Logger()
# logger = logger_instance.get_logger()
#

class BeckHealthServer(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup()

    def setup(self):
        # BeckHealthVectorStore.set_vector_ready(False)
        # BeckHealthVectorStore.clear_and_create_directory(vectorstore)
        #logger.info(vectorstore)
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #logger.info(f"App started at {start_time}")

    def run(self):
        '''
        Start the server with predefined host, port, and debug values.
        @param: None
        @return: None
        '''
        # BeckHealthVectorStore.set_vector_ready(False)
        # BeckHealthVectorStore.clear_and_create_directory(vectorstore)
        
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #logger.info(f"App started at {start_time}")
        super().run(host='0.0.0.0', port=5000, debug=True)
