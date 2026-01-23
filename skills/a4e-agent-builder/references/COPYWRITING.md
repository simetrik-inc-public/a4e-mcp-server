# A4E Copywriting Guide

Comprehensive guide for writing agent prompts, personality definitions, and UI microcopy.

---

## Part 1: Agent Prompts & Personality

### System Prompt Structure

The system prompt (`prompts/agent.md`) defines your agent's behavior. Use this structure:

```markdown
# Agent Name

Brief one-line description of who this agent is.

## Expertise

List the agent's core competencies:
- Primary skill area
- Secondary skill area
- Domain knowledge

## Personality

Define character traits:
- Tone (friendly, professional, casual)
- Communication style
- Unique quirks or characteristics

## Guidelines

Specific behavioral rules:
1. Always do X
2. Never do Y
3. When Z happens, respond with...

## Response Format

How to structure responses:
- Length preferences
- When to use views
- How to handle edge cases
```

### Personality Definition Patterns

**The Expert Friend**
```markdown
## Personality

You are a knowledgeable friend who happens to be an expert in [domain]. You:
- Explain complex topics in simple terms
- Use relatable analogies
- Celebrate user achievements
- Gently correct misconceptions without being condescending
```

**The Professional Assistant**
```markdown
## Personality

You are a professional [role] assistant. You:
- Maintain a courteous, business-appropriate tone
- Provide concise, actionable information
- Anticipate follow-up needs
- Respect the user's time
```

**The Enthusiastic Guide**
```markdown
## Personality

You are an enthusiastic guide passionate about [topic]. You:
- Share excitement about discoveries
- Encourage exploration and learning
- Use vivid descriptions
- Make even mundane tasks feel engaging
```

**The Calm Helper**
```markdown
## Personality

You are a calm, patient helper. You:
- Never show frustration
- Break complex tasks into steps
- Offer reassurance when users struggle
- Maintain composure during errors
```

### Tone Guidelines

| Tone | When to Use | Example |
|------|-------------|---------|
| **Friendly** | Consumer apps, casual contexts | "Great choice! Let me help you with that." |
| **Professional** | Business tools, enterprise | "I'll process your request now." |
| **Enthusiastic** | Gaming, creative tools | "Awesome! You're going to love this!" |
| **Supportive** | Health, finance, sensitive topics | "I understand. Let's work through this together." |
| **Direct** | Technical tools, power users | "Done. 3 files updated." |

### Response Formatting

**When to be brief:**
- Simple confirmations
- Yes/no questions
- Single data lookups

**When to be detailed:**
- Complex explanations
- Multi-step processes
- Error situations

**When to use views:**
- Displaying structured data
- Interactive elements needed
- Visual representation helps

### Skill Trigger Phrases

Write natural, varied triggers for skills:

**Good triggers:**
```yaml
triggers:
  - "show me my orders"
  - "where are my orders"
  - "order history"
  - "what did I buy"
  - "recent purchases"
```

**Why these work:**
- Varied sentence structures
- Different phrasings of same intent
- Natural language, not commands
- Include common misspellings/variations

**Bad triggers:**
```yaml
triggers:
  - "orders"           # Too vague
  - "SHOW_ORDERS"      # Unnatural
  - "display order list"  # Too formal
```

---

## Part 2: UI Microcopy

### Button Labels

**Action Buttons**
| Action | Good | Avoid |
|--------|------|-------|
| Save | "Save changes" | "Submit" |
| Delete | "Delete" or "Remove" | "Eliminate" |
| Cancel | "Cancel" | "Abort" |
| Create | "Create [item]" | "Add new" |
| Send | "Send message" | "Transmit" |

**Loading States**
```tsx
// During action
<Button disabled>
  <Loader className="animate-spin" />
  Saving...
</Button>

// Variations
"Processing..."
"Loading..."
"Sending..."
"Creating..."
```

**Success States**
```tsx
<Button disabled variant="success">
  <Check />
  Saved!
</Button>

// Variations
"Done!"
"Sent!"
"Created!"
"Complete!"
```

### Error Messages

**Structure:**
1. What happened (briefly)
2. Why it happened (if helpful)
3. What to do next

**Good error messages:**
```tsx
// Connection error
"Unable to connect. Check your internet and try again."

// Validation error
"Email address is invalid. Please use format: name@example.com"

// Not found
"We couldn't find that order. Double-check the order number."

// Permission error
"You don't have access to this feature. Contact your admin."

// Server error
"Something went wrong on our end. Please try again in a moment."
```

**Bad error messages:**
```tsx
// Too technical
"Error 500: Internal Server Error"

// Too vague
"An error occurred"

// Blaming user
"You entered invalid data"

// No solution
"Request failed"
```

**Error styling:**
```tsx
<div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
  <div className="flex items-center gap-2">
    <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
    <p className="text-sm text-red-400">
      Unable to save changes. Please try again.
    </p>
  </div>
</div>
```

### Empty States

**Structure:**
1. Friendly illustration/icon
2. Clear heading
3. Brief explanation
4. Action to resolve (if applicable)

**Examples:**

```tsx
// No results
<EmptyState
  icon={<Search className="h-12 w-12" />}
  title="No results found"
  description="Try adjusting your search or filters"
  action={<Button onClick={clearFilters}>Clear filters</Button>}
/>

// No items yet
<EmptyState
  icon={<Inbox className="h-12 w-12" />}
  title="No messages yet"
  description="Start a conversation to see messages here"
  action={<Button>New message</Button>}
/>

// Empty state after action
<EmptyState
  icon={<CheckCircle className="h-12 w-12" />}
  title="All caught up!"
  description="You've completed all your tasks"
/>
```

### Loading State Text

**Contextual loading messages:**
```tsx
// Generic
"Loading..."

// Specific actions
"Loading your dashboard..."
"Fetching latest data..."
"Preparing your report..."
"Connecting to server..."

// Long operations
"This may take a moment..."
"Almost there..."
"Processing large file..."
```

### Success Messages

**Toast notifications:**
```tsx
// Short confirmations
"Saved!"
"Sent successfully"
"Changes applied"

// With detail
"Order #1234 has been placed"
"Your profile has been updated"
"Message sent to 5 recipients"
```

**Inline success:**
```tsx
<div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
  <Check className="h-4 w-4 text-green-400" />
  <span className="text-sm text-green-400">Payment successful!</span>
</div>
```

### Form Validation Messages

**Field-level validation:**
```tsx
// Required field
"This field is required"

// Format validation
"Please enter a valid email address"
"Password must be at least 8 characters"
"Phone number should be 10 digits"

// Range validation
"Please enter a number between 1 and 100"
"Maximum 500 characters allowed"

// Match validation
"Passwords don't match"
```

**Form-level validation:**
```tsx
// Before submit
"Please fix the errors below to continue"

// After failed submit
"Unable to submit. Please review the highlighted fields."
```

### Tooltips & Help Text

**Input help text:**
```tsx
<div className="space-y-2">
  <Label>API Key</Label>
  <Input type="password" />
  <p className="text-xs text-muted-foreground">
    Find this in your account settings under Developer Options
  </p>
</div>
```

**Tooltips:**
```tsx
// Keep under 10 words
"Click to copy"
"Edit this item"
"Remove from list"
"View full details"

// With keyboard shortcut
"Save changes (Cmd+S)"
"Search (Cmd+K)"
```

### Confirmation Dialogs

**Destructive actions:**
```tsx
<AlertDialog>
  <AlertDialogContent>
    <AlertDialogHeader>
      <AlertDialogTitle>Delete this item?</AlertDialogTitle>
      <AlertDialogDescription>
        This action cannot be undone. This will permanently delete
        the item and all associated data.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter>
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction className="bg-destructive">
        Delete
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

**Non-destructive confirmations:**
```tsx
<Dialog>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Save changes?</DialogTitle>
      <DialogDescription>
        You have unsaved changes. Would you like to save them
        before leaving?
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button variant="outline">Don't save</Button>
      <Button>Save changes</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Placeholder Text

**Input placeholders:**
```tsx
// Descriptive
<Input placeholder="Enter your email address" />
<Input placeholder="Search products..." />
<Input placeholder="Type a message..." />

// With example format
<Input placeholder="e.g., john@example.com" />
<Input placeholder="YYYY-MM-DD" />
```

**Avoid:**
```tsx
// Too generic
<Input placeholder="Enter text here" />

// Redundant with label
<Label>Email</Label>
<Input placeholder="Email" />  // Don't repeat the label
```

---

## Writing Principles

### Be Concise
- Use short sentences
- Remove unnecessary words
- Get to the point quickly

### Be Clear
- Use simple language
- Avoid jargon unless domain-specific
- One idea per sentence

### Be Helpful
- Anticipate questions
- Provide next steps
- Offer alternatives when possible

### Be Consistent
- Use the same terms throughout
- Maintain consistent tone
- Follow established patterns

### Be Human
- Use contractions (it's, don't, we'll)
- Write like you speak
- Show personality appropriately

---

## Checklist

### Agent Prompts
- [ ] Clear expertise defined
- [ ] Personality traits specified
- [ ] Response format guidelines included
- [ ] Edge cases addressed
- [ ] Tone consistent throughout

### Skill Triggers
- [ ] 5+ varied trigger phrases
- [ ] Natural language used
- [ ] Common variations included
- [ ] No overly technical phrasing

### UI Microcopy
- [ ] Error messages are helpful
- [ ] Empty states guide users
- [ ] Button labels are action-oriented
- [ ] Loading states are contextual
- [ ] Confirmations are clear
