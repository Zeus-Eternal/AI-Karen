from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, connections, utility

COLLECTION_NAME = "case_memory_vectors"
DIM = 768  # align with your EmbeddingManager default (e.g., MPNet/E5)

def up(host: str = "milvus", port: str = "19530"):
    connections.connect("default", host=host, port=port)
    if utility.has_collection(COLLECTION_NAME):
        return
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=128, is_primary=True, auto_id=False),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=DIM),
    ]
    schema = CollectionSchema(fields, description="Case memory vectors (task/plan/outcome)")
    coll = Collection(COLLECTION_NAME, schema)
    coll.create_index(
        field_name="vector",
        index_params={"index_type": "HNSW", "metric_type": "IP", "params": {"M": 32, "efConstruction": 200}},
    )
    coll.load()

def down(host: str = "milvus", port: str = "19530"):
    connections.connect("default", host=host, port=port)
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)
