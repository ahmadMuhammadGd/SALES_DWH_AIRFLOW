import os
import shutil

class Read_landing:
    def __init__(self, landing_path):
        self.landing_path = landing_path
    
    def getFiles(self, extension:str):
        all_files = os.listdir(self.landing_path)
        filtered_files = [f for f in all_files if f.endswith(extension)]
        file_paths = [os.path.join(self.landing_path, f) for f in filtered_files]
        return file_paths
    
    def get_oldest_file(self, extension:str):
        file_paths = self.getFiles(extension)
        if not file_paths:
            return None
        oldest_file = min(file_paths, key=os.path.getctime)
        return oldest_file
    
    def get_newest_file(self, extension:str):
        file_paths = self.getFiles(extension)
        if not file_paths:
            return None
        newest_file = max(file_paths, key=os.path.getctime)
        return newest_file

# class Move_processed:
#     def __init__(self, processed_path):
#         self.processed_path = processed_path
    
#     def move(self, source_file_path:str):
#         if not os.path.exists(source_file_path):
#             raise FileNotFoundError(f"File not found: {source_file_path}")

#         file_name = os.path.split(source_file_path)[-1]
#         destination_path = os.path.join(self.processed_path, file_name)
#         shutil.move(source_file_path, destination_path)