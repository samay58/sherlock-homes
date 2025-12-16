# 🚀 Quick Start & Testing Guide

## Start Everything in 2 Minutes

### 1. Start Services
```bash
# Start all services
docker compose up --build

# Or use the Makefile
make dev
```

Wait for:
- API: http://localhost:8000
- Frontend: http://localhost:5173

### 2. Seed Sample Data
```bash
# Run migrations first (if needed)
docker compose exec api alembic upgrade head

# Seed sample listings
docker compose exec api python -m app.scripts.seed_data
```

### 3. Open the App
Visit: http://localhost:5173

## 🎨 What to Test

### Design System Features

1. **Homepage**
   - Notice the clean, minimal design
   - Typography hierarchy with Perfect Fourth scale
   - Smooth transitions under 200ms

2. **Listings Page** (`/listings`)
   - ✨ **Staggered animations** - Cards fade in sequentially
   - 🖱️ **Hover effects** - Cards lift with shadow
   - 🏷️ **Feature tags** - Turn blue on hover
   - 📸 **Image zoom** - Subtle scale on hover
   - 💀 **Skeleton loading** - Refresh to see loading states

3. **Listing Details** (click any card)
   - Clean layout with proper spacing
   - Image gallery (if multiple photos)
   - Feature flags displayed

4. **Criteria Page** (`/criteria`)
   - Form inputs with focus states
   - Blue focus rings on interaction
   - Smooth transitions

5. **Matches Page** (`/matches`)
   - Filtered results based on criteria
   - Same card interactions as listings
   - Match score display (if implemented)

## 🧪 Test Interactions

### Micro-Interactions to Notice
- **Card hover**: Lift + shadow + image zoom
- **Feature tags**: Color change on hover
- **Links**: Color transitions
- **Buttons**: Transform on hover/click
- **Forms**: Focus states with blue rings

### Dark Mode
Your system dark mode preference is automatically detected. Try switching your OS theme to see the design adapt.

### Responsive Design
- Resize browser window
- Test on mobile viewport
- Notice typography scaling

## 📝 Quick Tests

### Test API
```bash
# Health check
curl http://localhost:8000/ping

# Get listings
curl http://localhost:8000/listings

# Get test user criteria
curl http://localhost:8000/criteria/test-user
```

### Test Frontend Components
1. **Loading States**: Hard refresh any page
2. **Error States**: Disconnect network and navigate
3. **Empty States**: Filter with impossible criteria
4. **Animations**: Navigate between pages

## 🛠️ Development Tools

### Watch Logs
```bash
# All services
docker compose logs -f

# Just frontend
docker compose logs -f frontend

# Just API
docker compose logs -f api
```

### Make Commands
```bash
make help        # Show all commands
make logs        # Follow logs
make shell-api   # API shell
make shell-db    # Database shell
make test        # Run tests
```

### Hot Reload
- Frontend: Changes apply instantly
- Backend: API reloads on save

## 🎯 Key Features to Test

1. **Browse Listings**
   - Pagination
   - Price filtering
   - Bed/bath filtering

2. **Update Criteria**
   - Set min/max price
   - Choose feature priorities
   - Save and see matches update

3. **View Matches**
   - See filtered results
   - Check match scoring
   - Compare with criteria

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Clean restart
docker compose down -v
docker compose up --build
```

### Database Issues
```bash
# Reset database
make db-reset
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8000  # API
lsof -i :5173  # Frontend
lsof -i :5432  # Database
```

### Frontend Not Loading Design
- Hard refresh: Cmd+Shift+R (Mac) / Ctrl+Shift+R (PC)
- Clear browser cache
- Check console for errors

## 📊 Sample Data Details

The seed script creates:
- **30 listings** across SF neighborhoods
- **Varied prices**: $500k - $5M
- **Mixed features**: Some with natural light, outdoor space, etc.
- **Special properties**: First 3 are premium with all features
- **Test user criteria**: Pre-configured for good matches

## 🎨 Design Highlights

Look for these Rauno-inspired details:
- **Swiss minimalism**: Clean, focused on content
- **Layered shadows**: Multi-layer depth system
- **Perfect Fourth scale**: 1.333 typography ratio
- **8pt grid**: Consistent spacing
- **Instant feedback**: All interactions < 200ms
- **Thoughtful states**: Loading, hover, active, focus

## Next Steps

1. **Customize criteria** and see matches update
2. **Try different viewports** for responsive design
3. **Check dark mode** if you haven't
4. **Explore the codebase** - it's clean and well-documented!

---

**Need help?** Check `/docs` folder for detailed documentation.