"""
Shared constants for A4E package management.

These constants define which npm packages are provided by the A4E Hub view runtime
(via esm.sh CDN) and don't need to be declared in dependencies.json.

IMPORTANT: This must stay in sync with CORE_DEPENDENCIES in the A4E Hub frontend:
frontend/lib/api/views.ts
"""

# Core dependencies provided by A4E Hub view runtime.
# These are loaded via esm.sh CDN and don't need to be in dependencies.json.
# Source: frontend/lib/api/views.ts -> CORE_DEPENDENCIES
CORE_VIEW_DEPENDENCIES = frozenset({
    "react",
    "react-dom",
    "lucide-react",
    "framer-motion",
    "clsx",
    "tailwind-merge",
})

# Known external packages that views commonly use.
# These require declaration in dependencies.json (not in CORE_VIEW_DEPENDENCIES).
KNOWN_EXTERNAL_PACKAGES = frozenset({
    # Charts
    "recharts",
    "chart.js",
    "react-chartjs-2",
    # Dates
    "date-fns",
    "dayjs",
    "moment",
    "luxon",
    # State management
    "zustand",
    # Data fetching
    "axios",
    "swr",
    "react-query",
    "@tanstack/react-query",
    # Tables
    "@tanstack/react-table",
    # Forms
    "react-hook-form",
    "@hookform/resolvers",
    "zod",
    # UI components
    "@headlessui/react",
    "react-icons",
    # Utilities
    "lodash",
})

# Default versions for common packages.
# Used when adding packages to dependencies.json without explicit versions.
# Note: Packages in CORE_VIEW_DEPENDENCIES don't need versions here.
DEFAULT_PACKAGE_VERSIONS = {
    # Charts
    "recharts": "2.10.0",
    "chart.js": "4.4.0",
    "react-chartjs-2": "5.2.0",
    # Dates
    "date-fns": "3.0.0",
    "dayjs": "1.11.0",
    "moment": "2.30.0",
    "luxon": "3.4.0",
    # State management
    "zustand": "4.4.0",
    # Data fetching
    "axios": "1.6.0",
    "swr": "2.2.0",
    "@tanstack/react-query": "5.17.0",
    # Tables
    "@tanstack/react-table": "8.11.0",
    # Forms
    "react-hook-form": "7.49.0",
    "@hookform/resolvers": "3.3.0",
    "zod": "3.22.0",
    # UI components
    "@headlessui/react": "1.7.0",
    "react-icons": "5.0.0",
    # Utilities
    "lodash": "4.17.21",
}
