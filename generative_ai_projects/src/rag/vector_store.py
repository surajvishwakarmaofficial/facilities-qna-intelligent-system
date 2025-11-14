from pymilvus import MilvusClient
from typing import List, Tuple, Dict
import json
import time

class MilvusStore:
    def __init__(self, uri: str, token: str, collection_name: str = "yash_kb"):
        self.collection_name = collection_name
        self.client = MilvusClient(uri=uri, token=token, timeout=60)
        # print("Connected to Zilliz Cloud!")

        if self.collection_name not in self.client.list_collections():
            print(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                dimension=384,
                metric_type="L2",
                auto_id=True,
                enable_dynamic_field=True  # THIS IS THE KEY FOR SERVERLESS
            )
            # print("Collection created with dynamic fields.")

        # print("Collection loaded.")

    def add_documents(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict]):
        data = [
            {"embedding": e, "text": t, "metadata": json.dumps(m, ensure_ascii=False)}
            for t, e, m in zip(texts, embeddings, metadatas)
        ]
        res = self.client.insert(collection_name=self.collection_name, data=data)
        print(f"Inserted {res.insert_count} docs")
        time.sleep(1)
        return res

    def search(self, query_emb: List[float], top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        results = self.client.search(
            collection_name=self.collection_name,
            data=[query_emb],
            limit=top_k,
            output_fields=["text", "metadata"],
            search_params={"metric_type": "L2", "params": {"nprobe": 16}}
        )
        return [
            (hit.entity.get("text", ""), hit.distance, json.loads(hit.entity.get("metadata", "{}")))
            for hit in results[0]
        ]