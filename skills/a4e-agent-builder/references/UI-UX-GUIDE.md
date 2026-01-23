# A4E UI/UX Design Guide

Comprehensive design system and UI patterns for A4E agent views.

## Design System Overview

A4E uses a modern, dark-mode-first design system built on:
- **Tailwind CSS v4** with CSS variables
- **Radix UI** primitives for accessibility
- **Framer Motion** for animations
- **Lucide React** for icons

## Color System

### CSS Variables (HSL-based)

```css
:root {
  /* Light mode */
  --background: 0 0% 100%;
  --foreground: 0 0% 9%;
  --card: 0 0% 100%;
  --card-foreground: 0 0% 9%;
  --primary: 0 0% 9%;
  --primary-foreground: 0 0% 98%;
  --secondary: 0 0% 96%;
  --secondary-foreground: 0 0% 9%;
  --muted: 0 0% 96%;
  --muted-foreground: 0 0% 45%;
  --accent: 0 0% 96%;
  --accent-foreground: 0 0% 9%;
  --destructive: 0 84% 60%;
  --destructive-foreground: 0 0% 98%;
  --border: 0 0% 90%;
  --input: 0 0% 90%;
  --ring: 0 0% 9%;
}

.dark {
  --background: 0 0% 4%;
  --foreground: 0 0% 93%;
  /* ... inverted values */
}
```

### Semantic Colors

| Purpose | Light | Dark | Usage |
|---------|-------|------|-------|
| Success | `text-green-400` | `text-green-400` | Confirmations, positive feedback |
| Warning | `text-yellow-400` | `text-yellow-400` | Caution states |
| Error | `text-red-400` | `text-red-400` | Errors, destructive actions |
| Info | `text-blue-400` | `text-blue-400` | Informational messages |

---

## Core UI Components

### Button

```tsx
import { Button } from "@/components/ui/button";

// Variants
<Button variant="default">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="link">Link</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
<Button size="icon"><Icon /></Button>
```

**Styling Pattern:**
```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
  }
);
```

### Card

```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description text</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Main content */}
  </CardContent>
  <CardFooter>
    {/* Actions */}
  </CardFooter>
</Card>
```

**Styling:**
- Card: `rounded-lg border bg-card text-card-foreground shadow-sm`
- Header: `flex flex-col space-y-1.5 p-6`
- Title: `text-2xl font-semibold leading-none tracking-tight`
- Description: `text-sm text-muted-foreground`
- Content: `p-6 pt-0`
- Footer: `flex items-center p-6 pt-0`

### Input

```tsx
import { Input } from "@/components/ui/input";

<Input
  type="text"
  placeholder="Enter value..."
  className="w-full"
/>
```

**Styling:**
```tsx
className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
```

### Badge

```tsx
import { Badge } from "@/components/ui/badge";

<Badge variant="default">Default</Badge>
<Badge variant="secondary">Secondary</Badge>
<Badge variant="destructive">Destructive</Badge>
<Badge variant="outline">Outline</Badge>
```

**Styling:**
- Base: `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors`

### Dialog/Modal

```tsx
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

<Dialog>
  <DialogTrigger asChild>
    <Button>Open</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    {/* Content */}
    <DialogFooter>
      <Button>Save</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**Animation:**
- Open: `animate-in fade-in-0 zoom-in-95`
- Close: `animate-out fade-out-0 zoom-out-95`

---

## Animation Patterns

### Framer Motion Basics

```tsx
import { motion, AnimatePresence } from "framer-motion";

// Fade in
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}
  transition={{ duration: 0.3 }}
>
  Content
</motion.div>

// Scale + Fade
<motion.div
  initial={{ opacity: 0, scale: 0.95 }}
  animate={{ opacity: 1, scale: 1 }}
  transition={{ duration: 0.2, ease: "easeOut" }}
>
  Content
</motion.div>

// Slide in from bottom
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  Content
</motion.div>
```

### Typing Animation

```tsx
// Character-by-character typing
const [displayedText, setDisplayedText] = useState("");

useEffect(() => {
  let index = 0;
  const interval = setInterval(() => {
    setDisplayedText(text.slice(0, index + 1));
    index++;
    if (index >= text.length) clearInterval(interval);
  }, 50); // 50ms per character
  return () => clearInterval(interval);
}, [text]);

// Blinking cursor
<motion.span
  animate={{ opacity: [0, 1, 0] }}
  transition={{ duration: 0.8, repeat: Infinity }}
  className="inline-block w-[2px] h-[1em] bg-current ml-1"
/>
```

### Hover Effects

```tsx
<motion.div
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  transition={{ type: "spring", stiffness: 400, damping: 17 }}
>
  Interactive element
</motion.div>
```

### Staggered Lists

```tsx
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

<motion.ul variants={container} initial="hidden" animate="show">
  {items.map(i => (
    <motion.li key={i} variants={item}>{i}</motion.li>
  ))}
</motion.ul>
```

---

## State Patterns

### Loading States

```tsx
// Skeleton loading
<div className="h-4 w-32 bg-muted rounded animate-pulse" />
<div className="h-4 w-24 bg-muted rounded animate-pulse" />

// Button loading
<Button disabled>
  <Loader className="w-4 h-4 mr-2 animate-spin" />
  Loading...
</Button>

// Full page loading
<div className="flex items-center justify-center h-full">
  <Loader className="w-8 h-8 animate-spin text-muted-foreground" />
</div>
```

### Empty States

```tsx
<div className="rounded-lg border border-dashed p-12 text-center">
  <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
  <h3 className="text-lg font-medium mb-1">No messages yet</h3>
  <p className="text-sm text-muted-foreground mb-4">
    Start a conversation to see messages here
  </p>
  <Button>Start Chat</Button>
</div>
```

### Error States

```tsx
// Inline error
<div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
  <p className="text-sm text-red-400">{error}</p>
</div>

// Error with icon
<div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
  <AlertCircle className="h-4 w-4 text-destructive" />
  <p className="text-sm text-destructive">{error}</p>
</div>
```

### Success States

```tsx
<div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
  <Check className="h-4 w-4 text-green-400" />
  <p className="text-sm text-green-400">Operation successful!</p>
</div>
```

---

## Form Patterns

### Basic Form

```tsx
<form onSubmit={handleSubmit} className="space-y-4">
  <div className="space-y-2">
    <label htmlFor="name" className="text-sm font-medium">
      Name
    </label>
    <Input
      id="name"
      value={name}
      onChange={(e) => setName(e.target.value)}
      placeholder="Enter name..."
    />
  </div>

  <div className="flex justify-end gap-2">
    <Button type="button" variant="outline" onClick={onCancel}>
      Cancel
    </Button>
    <Button type="submit" disabled={isSubmitting}>
      {isSubmitting ? "Saving..." : "Save"}
    </Button>
  </div>
</form>
```

### Input with Validation

```tsx
<div className="space-y-2">
  <label htmlFor="email" className="text-sm font-medium">
    Email
  </label>
  <Input
    id="email"
    type="email"
    value={email}
    onChange={(e) => setEmail(e.target.value)}
    className={error ? "border-destructive" : ""}
  />
  {error && (
    <p className="text-xs text-destructive">{error}</p>
  )}
</div>
```

---

## Accessibility Patterns

### Focus Management

```tsx
// Focus visible ring
className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"

// Skip to main content
<a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:p-4">
  Skip to main content
</a>
```

### Screen Reader Text

```tsx
// Hidden but accessible
<span className="sr-only">Close dialog</span>

// Icon-only button
<Button size="icon" aria-label="Delete item">
  <Trash className="h-4 w-4" />
</Button>
```

### Keyboard Navigation

```tsx
// Handle keyboard events
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    handleAction();
  }
  if (e.key === "Escape") {
    handleClose();
  }
};
```

---

## Icon System

### Lucide React Usage

```tsx
import { Search, Plus, X, ChevronDown, Check, AlertCircle } from "lucide-react";

// Standard sizes
<Icon className="h-4 w-4" />  // Small (in buttons, badges)
<Icon className="h-5 w-5" />  // Medium (standalone)
<Icon className="h-6 w-6" />  // Large (headings)
<Icon className="h-8 w-8" />  // XL (empty states)

// With text
<div className="flex items-center gap-2">
  <Search className="h-4 w-4 text-muted-foreground" />
  <span>Search</span>
</div>

// Prevent shrinking
<Icon className="h-4 w-4 flex-shrink-0" />
```

### Common Icons

| Icon | Usage |
|------|-------|
| `Search` | Search inputs |
| `Plus` | Add actions |
| `X` | Close, remove |
| `Check` | Success, selected |
| `AlertCircle` | Errors, warnings |
| `ChevronDown` | Dropdowns |
| `Loader` | Loading (with animate-spin) |
| `Trash` | Delete |
| `Edit` | Edit actions |
| `Eye` / `EyeOff` | Show/hide password |

---

## Spacing & Layout

### Spacing Scale

```tsx
// Padding
p-2   // 8px - Tight
p-3   // 12px - Compact
p-4   // 16px - Default
p-6   // 24px - Spacious

// Gaps
gap-2  // 8px - Between small items
gap-3  // 12px - Default gap
gap-4  // 16px - Larger gap
gap-6  // 24px - Section gap

// Stack spacing
space-y-2  // 8px vertical
space-y-4  // 16px vertical
space-y-6  // 24px vertical
```

### Responsive Breakpoints

```tsx
// Mobile first
<div className="p-4 md:p-6 lg:p-8">
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {/* Items */}
  </div>
</div>
```

| Breakpoint | Width | Usage |
|------------|-------|-------|
| (default) | < 640px | Mobile |
| `sm:` | 640px | Large phones |
| `md:` | 768px | Tablets |
| `lg:` | 1024px | Laptops |
| `xl:` | 1280px | Desktops |
| `2xl:` | 1536px | Large screens |

---

## Utility Function

### Class Merge (cn)

```tsx
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage
<div className={cn(
  "base-class",
  variant === "primary" && "primary-class",
  className
)}>
```

---

## Data Display Patterns

### Score/Rating Display

```tsx
const getScoreColor = (score: number) => {
  if (score < 0.5) return "text-red-400";
  if (score < 0.8) return "text-yellow-400";
  return "text-green-400";
};

<span className={cn("font-medium", getScoreColor(score))}>
  {(score * 100).toFixed(0)}%
</span>
```

### Priority Badges

```tsx
const priorityStyles = {
  high: "bg-red-500/20 text-red-300 border-red-500/30",
  medium: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  low: "bg-green-500/20 text-green-300 border-green-500/30",
};

<Badge className={priorityStyles[priority]}>
  {priority}
</Badge>
```

### Tables

```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
      <TableHead className="text-right">Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {items.map((item) => (
      <TableRow key={item.id} className="hover:bg-muted/50">
        <TableCell>{item.name}</TableCell>
        <TableCell>
          <Badge>{item.status}</Badge>
        </TableCell>
        <TableCell className="text-right">
          <Button size="sm" variant="ghost">Edit</Button>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```
