# Mapbox Integration

The Property Finder Map View uses Mapbox GL JS to display an interactive map with property markers.

## Setup

### 1. Get a Mapbox Access Token

1. Visit https://account.mapbox.com/
2. Sign up for a free account or log in
3. Go to **Access Tokens** in your account dashboard
4. Copy your **Default public token** or create a new one

### 2. Configure the Token

Create a `.env.local` file in the `frontend/` directory:

```bash
NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_actual_token_here
```

You can use the `.env.local.example` file as a template.

### 3. Restart the Development Server

After adding the token, restart your Next.js dev server:

```bash
npm run dev
```

## Features

### Interactive Map
- **Pan & Zoom**: Navigate the map to explore different areas
- **3D Buildings**: Maps display with a 45° pitch for depth
- **Navigation Controls**: Zoom in/out and compass controls
- **Fullscreen Mode**: Toggle fullscreen view
- **Scale Indicator**: Distance scale for reference

### Property Markers
- **Color-coded**: Blue for sale properties, green for rentals
- **Price Display**: Shows property price directly on the marker
- **Click to View**: Click any marker to see detailed property information
- **Auto-zoom**: Map automatically zooms to show all properties
- **Hover Effect**: Markers scale up on hover

### Property Detail Cards
- **Property Image**: Large hero image at the top
- **Key Details**: Price, beds, baths, square footage
- **Location**: Full address display
- **Amenities**: Nearby amenities with distances
- **External Link**: Opens full property listing in a new tab
- **Close Button**: Easy dismissal of detail cards

## Usage

1. Search for properties in the chat panel (e.g., "Show me properties in SW1")
2. Switch to the **Property Finder** tab in the sidebar
3. Toggle to **Map View** using the List/Map buttons
4. Browse properties on the interactive map
5. Click markers to view detailed information
6. Click "View Details" to open the full listing

## Customization

### Map Style
Change the map style in `PropertyMapView.tsx`:

```typescript
style: 'mapbox://styles/mapbox/streets-v12'  // Default
// Options: streets-v12, light-v11, dark-v11, satellite-v9, satellite-streets-v12
```

### Marker Colors
Customize marker colors in the `useEffect` that creates markers:

```typescript
background: ${property.type === 'sale' ? '#3b82f6' : '#10b981'}
```

### Default Location
Change the default center (currently London):

```typescript
const defaultCenter: [number, number] = center || [-0.1276, 51.5074];
```

## Troubleshooting

### Map Not Displaying
- Ensure your Mapbox token is set in `.env.local`
- Check the browser console for error messages
- Verify the token starts with `pk.`

### Properties Not Showing
- Ensure properties have `lat` and `lng` coordinates
- If coordinates are missing, the component generates random locations near London
- Check that property data is being passed to the component

### Performance Issues
- Consider implementing marker clustering for large datasets
- Reduce map pitch or disable 3D buildings for better performance

## Next.js Considerations

The component uses `"use client"` directive for client-side rendering. Mapbox GL JS requires browser APIs and cannot be server-rendered.

## Browser Support

Mapbox GL JS requires WebGL 2.0 support:
- Chrome 56+
- Firefox 51+
- Safari 15+
- Edge 79+

Internet Explorer is **not supported**.
