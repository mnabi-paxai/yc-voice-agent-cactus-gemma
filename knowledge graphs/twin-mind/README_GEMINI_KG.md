# Knowledge Graph Builder with Gemini

## ✅ Setup Complete!

Your local knowledge graph system is ready to use with Google Gemini.

### What's Installed:
- ✅ LlamaIndex with Gemini support
- ✅ Local graph storage (no Docker needed)
- ✅ Environment variable support (.env file)
- ✅ Interactive query interface

## Quick Start

### 1. Create .env File

```bash
cd "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind"
cp .env.example .env
```

### 2. Add Your Gemini API Key

Edit the `.env` file and add your key:

```bash
GEMINI_API_KEY=your-actual-gemini-api-key-here
```

**Get your API key here:** https://makersuite.google.com/app/apikey

### 3. Run the Knowledge Graph Builder

```bash
python3 run_kg.py
```

## Features

### ✅ Local Storage
- No Docker required
- Saves to `./graph_storage` folder
- Fast reload on subsequent runs

### ✅ Real-time Updates
- Add new PDFs anytime
- Incremental updates
- Persistent storage

### ✅ Interactive Queries
- Natural language questions
- Built-in example queries
- Multiple query modes

### ✅ Secure
- API key in .env file (not in code)
- .env is gitignored by default

## Usage Examples

### First Time Setup
```bash
# 1. Create .env file
cp .env.example .env

# 2. Edit .env and add your GEMINI_API_KEY

# 3. Run the builder
python3 run_kg.py
```

The script will:
1. Load DeepSeekMath.pdf
2. Build knowledge graph (2-5 minutes)
3. Save to `./graph_storage`
4. Start interactive query mode

### Query Existing Graph
```bash
python3 run_kg.py
# Choose option 1: Load and query existing graph
```

### Add New PDF
```bash
python3 run_kg.py
# Choose option 2: Add new PDF to graph
```

### Delete and Rebuild
```bash
python3 run_kg.py
# Choose option 3: Delete graph and start fresh
```

## Why Gemini?

| Feature | Gemini 1.5 Flash | GPT-4 |
|---------|------------------|-------|
| **Speed** | ⚡ Very fast | Slower |
| **Cost** | 💰 Free tier available | Paid only |
| **Context** | 1M tokens | 128K tokens |
| **API** | Free to start | Requires payment |

## File Structure

```
twin-mind/
├── .env                          # Your API key (DO NOT COMMIT)
├── .env.example                  # Template for .env
├── knowledge_graph_simple.py     # Core graph builder
├── run_kg.py                     # Interactive interface
├── graph_storage/                # Saved graphs
│   ├── docstore.json
│   ├── graph_store.json
│   └── index_store.json
└── DeepSeekMath.pdf             # Example PDF
```

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure you created `.env` file (not `.env.example`)
- Check that `.env` contains: `GEMINI_API_KEY=your-key`
- Run from the correct directory

### "Module not found"
```bash
pip3 install llama-index llama-index-llms-gemini llama-index-embeddings-gemini python-dotenv
```

### "Out of memory"
- Reduce chunk_size in `knowledge_graph_simple.py`
- Process smaller PDFs
- Close other applications

### Graph takes too long to build
- First build takes 2-5 minutes (normal)
- Subsequent loads are instant
- Consider using Gemini 1.5 Flash (default, fastest)

## API Key Security

✅ **Safe:**
- Store in `.env` file
- `.env` is automatically gitignored
- Not visible in code or commits

❌ **Never:**
- Commit `.env` to git
- Share your API key
- Hard-code the key in scripts

## Next Steps

1. **Create your .env file** with Gemini API key
2. **Run:** `python3 run_kg.py`
3. **Query your knowledge graph!**

## Support

- Gemini API Docs: https://ai.google.dev/docs
- LlamaIndex Docs: https://docs.llamaindex.ai
- Get API Key: https://makersuite.google.com/app/apikey
