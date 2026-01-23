# Mobile Views Guide

A4E has first-class mobile support built into the view system. This guide covers mobile-optimized view development.

## Automatic Mobile Detection

The A4E Hub automatically detects mobile devices and passes the `isMobile` prop to all views:

```tsx
interface ViewProps {
  isMobile?: boolean;  // Auto-injected, true when viewport < 768px
  // ... your custom props
}
```

## Mobile View Template

When creating views with `add_view`, set `mobile_optimized=true` to get this template:

```tsx
"use client";

import React from "react";

interface ViewProps {
  isMobile?: boolean;
  // Add your props here
}

export default function MyView({ isMobile, ...props }: ViewProps) {
  return (
    <div className={`
      w-full max-w-4xl mx-auto
      ${isMobile ? 'p-3' : 'p-6'}
    `}>
      {/* Mobile-first responsive grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {/* Content */}
      </div>

      {/* Mobile bottom action bar */}
      {isMobile && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t safe-area-inset-bottom">
          {/* Actions */}
        </div>
      )}
    </div>
  );
}
```

## Responsive Design Patterns

### Grid Layouts

```tsx
// Responsive columns
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">

// Mobile stack, desktop side-by-side
<div className="flex flex-col md:flex-row gap-4">

// Mobile full-width, desktop contained
<div className="w-full md:w-auto md:max-w-md">
```

### Spacing & Padding

```tsx
// Responsive padding
<div className="p-3 sm:p-4 md:p-6 lg:p-8">

// Bottom padding for action bars (mobile)
<div className={isMobile ? 'pb-20' : 'pb-4'}>

// Responsive margins
<div className="mx-2 sm:mx-4 md:mx-6">
```

### Typography

```tsx
// Responsive text sizes
<h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl">

// Mobile-optimized body text
<p className="text-sm sm:text-base md:text-lg">

// Truncate on mobile
<span className={`${isMobile ? 'truncate max-w-[200px]' : ''}`}>
```

### Touch Targets

```tsx
// Minimum 44px touch target
<button className="min-h-[44px] min-w-[44px] p-3">

// Touch-friendly spacing
<div className="space-y-3 sm:space-y-2">

// Larger tap areas on mobile
<a className={`p-${isMobile ? '4' : '2'}`}>
```

## Mobile-Specific Patterns

### Fixed Bottom Action Bar

```tsx
{isMobile && (
  <div className="
    fixed bottom-0 left-0 right-0
    p-4 bg-white border-t
    safe-area-inset-bottom
    z-50
  ">
    <button className="w-full py-3 bg-blue-600 text-white rounded-lg">
      Primary Action
    </button>
  </div>
)}
```

### Swipeable Cards

```tsx
<div className="
  overflow-x-auto
  flex gap-4
  snap-x snap-mandatory
  touch-pan-x
  -mx-4 px-4
">
  {items.map(item => (
    <div key={item.id} className="
      flex-shrink-0
      w-[280px]
      snap-center
    ">
      {/* Card content */}
    </div>
  ))}
</div>
```

### Collapsible Sections

```tsx
const [expanded, setExpanded] = useState(!isMobile);

<div>
  <button
    onClick={() => setExpanded(!expanded)}
    className="flex justify-between items-center w-full p-4"
  >
    <span>Section Title</span>
    <ChevronDown className={`transform ${expanded ? 'rotate-180' : ''}`} />
  </button>
  {expanded && <div className="p-4">{/* Content */}</div>}
</div>
```

### Mobile Modal/Drawer

```tsx
{showModal && (
  <div className={`
    fixed inset-0 z-50
    ${isMobile
      ? 'flex items-end'  // Bottom sheet on mobile
      : 'flex items-center justify-center'  // Center modal on desktop
    }
  `}>
    <div className="absolute inset-0 bg-black/50" onClick={close} />
    <div className={`
      relative bg-white
      ${isMobile
        ? 'w-full rounded-t-2xl max-h-[80vh]'
        : 'w-full max-w-md rounded-xl mx-4'
      }
    `}>
      {/* Modal content */}
    </div>
  </div>
)}
```

## Mobile View Modes

A4E Hub supports two mobile view modes:

- **video**: Shows avatar video feed
- **chat**: Shows chat interface with views

The frontend automatically handles toggling between these modes.

## iOS Safe Areas

Handle notches and home indicators:

```tsx
// Bottom safe area
<div className="pb-safe-area-inset-bottom">

// Or use padding utility
<div className="pb-[env(safe-area-inset-bottom)]">
```

## Touch Gestures

```tsx
// Enable horizontal panning
<div className="touch-pan-x overflow-x-auto">

// Enable vertical panning
<div className="touch-pan-y overflow-y-auto">

// Disable touch actions (for custom gestures)
<div className="touch-none">
```

## Performance Tips

1. **Lazy load images**: Use Next.js Image component with `loading="lazy"`
2. **Virtualize long lists**: Use `react-window` for 50+ items
3. **Reduce animations on mobile**: Check `prefers-reduced-motion`
4. **Minimize re-renders**: Use `React.memo` for list items

```tsx
// Check for reduced motion preference
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Conditional animation
<div className={prefersReducedMotion ? '' : 'animate-fade-in'}>
```

## Testing Mobile Views

1. Use Chrome DevTools mobile emulation
2. Test on real devices when possible
3. Check both portrait and landscape orientations
4. Test with different font sizes (accessibility)
5. Verify touch targets are at least 44x44px

## Common Breakpoints

| Breakpoint | Width | Use Case |
|------------|-------|----------|
| `sm` | 640px | Large phones, landscape |
| `md` | 768px | Tablets |
| `lg` | 1024px | Small laptops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large screens |

## Checklist for Mobile-Optimized Views

- [ ] Uses `isMobile` prop for conditional rendering
- [ ] Responsive grid with mobile-first columns
- [ ] Touch targets minimum 44px
- [ ] Bottom padding for action bars (`pb-20`)
- [ ] Text is readable without zooming
- [ ] Horizontal scrolling uses snap points
- [ ] Fixed elements account for safe areas
- [ ] Images are lazy loaded
- [ ] Animations respect reduced motion preference
