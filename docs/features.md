# Features

OpsDeck is built for FastAPI developers who want a strong default and room to grow into more advanced workflows.

## 🔮 Smart Selects

Dealing with Foreign Keys in admin panels is usually a pain. You get a dropdown with `Object <1>` or have to write custom queries.

**OpsDeck** changes that.

- **Auto-Detection**: We automatically detect `ForeignKey` columns in your SQLAlchemy models.
- **Searchable Dropdowns**: Instead of a plain `<select>`, you get a searchable, AJAX-powered widget.
- **No Config**: It generally "just works". If you define `__admin_repr__` on your model, we use it.

```python
class Author(Base):
    __tablename__ = "authors"
    name = Column(String)
    
    def __admin_repr__(self):
        return self.name  # Use this in dropdowns
```

## 🧪 Advanced Filtering

Sidebar filters are generated automatically based on your model configuration.

```python
admin.register(
    Product,
    filter_fields=["available", "created_at", "price"],
)
```

- **Boolean**: Toggle switches for `True/False` fields.
- **Relationships**: Filter by related objects (e.g., "Show products in 'Tech' category").
- **Operators**: Support for `__gte`, `__lte` (Greater/Less than) suffix magic.

## 📊 System Observability

Your admin panel is the cockpit of your application. It should show you how the engine is running.

**The Dashboard includes:**
- **CPU Usage**: Real-time load monitoring.
- **Memory**: RAM consumption.
- **Disk I/O**: Storage checks.

All rendered with slick, animated progress bars that fit the cyberpunk aesthetic.

## 💾 CSV Export (Streaming)

Need to dump data? 

- **Streaming Response**: We stream data row-by-row, so you can export 100,000 users without blowing up your server RAM.
- **Filter-Aware**: Exports exactly what you see on the screen (current search + active filters).

## Permissions And Security

We take security seriously.

- **URL Signing**: Polymorphic form loads use signed URLs to prevent IDOR attacks.
- **CSP Headers**: Strict Content Security Policy injected automatically.
- **Rate Limiting**: Login endpoints are protected against brute-force.
