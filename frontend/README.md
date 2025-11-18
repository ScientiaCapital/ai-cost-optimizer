# AI Cost Optimizer - Frontend Integration

Real-time dashboard for monitoring AI routing decisions powered by Supabase Realtime.

## 🚀 Quick Start

### 1. Configure Your Credentials

Edit `realtime-dashboard.html` and update line 159:

```javascript
const SUPABASE_URL = 'https://nhjhzzkcqtsmfgvairos.supabase.co'  // Your Supabase URL
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY_HERE'  // Replace with your anon key
```

### 2. Serve Locally

```bash
# Option 1: Python HTTP server
python3 -m http.server 8080

# Option 2: Node.js HTTP server
npx http-server -p 8080

# Option 3: PHP built-in server
php -S localhost:8080
```

### 3. Open in Browser

```
http://localhost:8080/realtime-dashboard.html
```

## 📊 Features

- **Real-Time Updates**: Live routing decisions via Supabase Realtime
- **Statistics Dashboard**: Total requests, cost savings, cache hit rate
- **Confidence Tracking**: Average confidence scores across decisions
- **Secure**: XSS-safe DOM manipulation (no innerHTML)
- **Responsive**: Works on desktop and mobile devices

## 🎨 Customization

### Change Color Scheme

Edit the CSS gradient in line 16:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Adjust Update Frequency

The dashboard updates in real-time. To filter metrics:

```javascript
// Only show high-cost decisions
.on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'routing_metrics',
    filter: 'cost=gt.0.01'  // Only costs > $0.01
}, callback)
```

### Modify Stats Calculations

Edit the `updateStats()` function (lines 232-259):

```javascript
function updateStats(metric) {
    // Custom logic here
    // E.g., different cost savings calculation
    const potentialCost = metric.cost * 5  // Assume 5x savings
    const saved = potentialCost - metric.cost
    totalCostSaved += saved
}
```

## 🔐 Authentication (Optional)

To show only authenticated user's metrics:

```javascript
// Login first
const { data, error } = await supabaseClient.auth.signInWithPassword({
    email: 'user@example.com',
    password: 'password'
})

// Metrics will automatically filter by user_id via RLS
```

## 📦 Deployment

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel
```

### Deploy to Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
cd frontend
netlify deploy --prod
```

### Deploy to GitHub Pages

```bash
# Push frontend folder to gh-pages branch
git subtree push --prefix frontend origin gh-pages

# Access at: https://yourusername.github.io/ai-cost-optimizer
```

## 🧪 Testing

1. **Trigger a routing decision** via API:
   ```bash
   curl -X POST https://your-api-url/complete \
     -H "Content-Type: application/json" \
     -d '{"prompt": "What is AI?", "max_tokens": 100}'
   ```

2. **Watch the dashboard update** in real-time! ✨

## 📚 Learn More

- [Supabase Realtime Documentation](https://supabase.com/docs/guides/realtime)
- [Backend Integration](../docs/REALTIME_SETUP.md)
- [API Documentation](http://your-api-url/docs)

---

**Built with ❤️ using Supabase Realtime**
