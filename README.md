# Platebook Generator 📚

Generate beautiful, print-ready platebooks from Google Sheets with pixel-perfect quality.

## 🌐 Web Interface (Quick Preview)

**Live Demo:** [https://YOUR-USERNAME.github.io/platebook](https://YOUR-USERNAME.github.io/platebook)

Use the web interface for:
- Quick previews
- Testing layouts
- Sharing with others

## 🎯 GitHub Actions (Perfect Quality PDFs)

For production-quality PDFs:

1. Go to **Actions** tab
2. Click **"Generate Platebook PDF"**
3. Click **"Run workflow"**
4. Enter your Google Sheet CSV URL
5. Click **"Run workflow"**
6. Download PDF from **Releases** or **Artifacts**

## 💻 Local Usage

### Prerequisites
```bash
pip install reportlab requests
```

### Generate from Google Sheets
```bash
python3 make_platebook.py
```

### Generate from local CSV
```bash
python3 platebook.py lessons.json output.pdf
```

## 📋 Google Sheet Format

Your Google Sheet should have these columns:

| Plate | Title | Date |
|-------|-------|------|
| 1 | Introduction to the class, geography of East Asia | Jan 6 |
| 2 | East Asian Language, Religion, Culture | Jan 8 |
| ... | ... | ... |

**To publish:**
1. File → Share → Publish to web
2. Choose "Entire Document"
3. Format: "Comma-separated values (.csv)"
4. Copy the URL

## 📁 Files

- `platebook.py` - Core PDF generator (pixel-perfect)
- `make_platebook.py` - Interactive CLI tool
- `platebook_generator.html` - Web interface
- `.github/workflows/generate-platebook.yml` - GitHub Actions workflow

## 🚀 Deployment

### GitHub Pages
1. Push this repo to GitHub
2. Go to Settings → Pages
3. Source: Deploy from branch `main`
4. Folder: `/` (root)
5. Save

Your web interface will be live at:
`https://YOUR-USERNAME.github.io/platebook`

### GitHub Actions
Already configured! Just run the workflow from the Actions tab.

## 📖 Example

```bash
# Interactive mode
python3 make_platebook.py

# Direct mode
python3 platebook.py lessons_hist213_w26.json HIST213_Platebook.pdf
```

## 🎨 Features

- ✅ Pixel-perfect PDF generation
- ✅ Google Sheets integration
- ✅ Web preview interface
- ✅ Automated GitHub Actions
- ✅ Cover page & Table of Contents
- ✅ Custom layouts (Person/Place/Thing, Timeline, Map, Questions)
- ✅ Print-optimized for letter size

## 📝 License

MIT License - Feel free to use and modify!

---

**Made with ❤️ for HIST 213 East Asia in the Modern World**
