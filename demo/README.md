# OpsDeck - Live Demo

🎯 **Live Demo:** [https://your-project.vercel.app](https://your-project.vercel.app)

## Features Showcased

✨ **Matrix UI Theme** - Stunning green/black aesthetic with terminal-style typography  
🔍 **Auto-Discovery** - 4 models registered with just `admin.auto_discover(Base)`  
📝 **Full CRUD** - Create, Read, Update, Delete operations  
🔎 **Search & Filter** - Real-time search across all models  
📄 **Pagination** - Smooth navigation through large datasets  
🎨 **Responsive Design** - Works on desktop, tablet, and mobile

## Models in Demo

1. **BlogPost** - Articles with title, content, author, views
2. **Product** - E-commerce items with pricing and stock
3. **Author** - Writer profiles with bio and activity status
4. **Category** - Content organization tags

## Local Development

```bash
# Install dependencies
pip install -e ..

# Run demo
cd demo
python app.py
```

Visit: http://localhost:8000/admin

## Deployment to Vercel

### Option 1: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Option 2: GitHub Integration

1. Push to GitHub
2. Import project in Vercel dashboard
3. Deploy automatically

### Option 3: Vercel Button

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/opsdeck)

## Configuration

### Environment Variables (Optional)

- `SECRET_KEY` - Admin secret key (defaults to demo key)
- `DATABASE_URL` - Database connection (defaults to SQLite)
- `READONLY_MODE` - Set to `true` for public demos

### Read-Only Models

To keep specific models view-only in a public demo:

```python
admin.register(BlogPost, readonly=True)
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy 2.0** - Async ORM
- **Jinja2** - Template engine
- **Tailwind CSS** - Utility-first CSS
- **Chart.js** - Dashboard visualizations
- **HTMX** - Dynamic interactions

## Performance

- ⚡ **First Load:** <2 seconds
- 🚀 **Navigation:** Instant (HTMX)
- 📦 **Bundle Size:** Minimal (CDN-based)
- 🔄 **Database:** SQLite (serverless-compatible)

## Screenshots

### Dashboard
![Matrix Dashboard](../artifacts/matrix_sidebar_dashboard.png)

### List View
![Matrix List](../artifacts/matrix_sidebar_list.png)

### Create Form
![Matrix Create](../artifacts/create_form_test.png)

## Learn More

- [GitHub Repository](https://github.com/yourusername/opsdeck)
- [Documentation](https://github.com/yourusername/opsdeck#readme)
- [PyPI Package](https://pypi.org/project/opsdeck/)

## License

MIT License - see [LICENSE](../LICENSE.md)
