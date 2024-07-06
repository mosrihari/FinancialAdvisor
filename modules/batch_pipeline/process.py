class Process(BaseModel):
    author:str
    content:str
    created_at:datetime
    headline:str
    id:int
    images:List[str]
    source:str
    summary:str
    symbols:List[str]
    updated_at:datetime
    url:str

    def to_document(self):
        print(self.content)
        cleaned_text = clean(self.content)
        return cleaned_text
