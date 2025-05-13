from pinecone import Pinecone

class VectorService:
    def __init__(self, api_key, index_name):
        """Pinecone 초기화"""
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
    
    def search_properties(self, top_k=500):
        """Pinecone에서 매물 검색"""
        try:
            print("Pinecone에서 매물 검색 시작")
            resp = self.index.query(vector=[0.0]*1536, top_k=top_k, include_metadata=True)
            print(f"Pinecone 검색 결과: {len(resp.matches)}개 매물")
            return resp.matches
        except Exception as e:
            print(f"Pinecone 검색 오류: {e}")
            # 오류 발생 시 빈 리스트 반환
            return []