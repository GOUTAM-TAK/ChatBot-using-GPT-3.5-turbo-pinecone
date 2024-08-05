from utils.config import tokenizer,summerize_model

def summarize_text(query, text_chunk):
    # Template to wrap the user query and text chunk
    input_text = f"Summarize the following text based on the query: {query}\n\nText: {text_chunk}"
    
    inputs = tokenizer.encode(input_text, return_tensors='pt', max_length=1024, truncation=True)
    summary_ids = summerize_model.generate(inputs, max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    
    return summary

def chunk_text(text, chunk_size=1024):
    tokens = tokenizer.encode(text)
    chunks = [tokens[i:i+chunk_size] for i in range(0, len(tokens), chunk_size)]
    return [tokenizer.decode(chunk, skip_special_tokens=True) for chunk in chunks]