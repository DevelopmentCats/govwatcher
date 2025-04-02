# GovWatcher Frontend Plan

## Overview
This plan outlines the frontend implementation for GovWatcher, a web application that monitors and archives .gov websites and government social media accounts. The frontend will provide an intuitive, professional interface for users to explore archived websites, view changes over time, and receive notifications about significant updates.

## Design Goals
- **Professional & Modern UI**: Clean, authoritative aesthetic appropriate for government data
- **Intuitive Navigation**: Easy exploration of complex archive data
- **Responsive Design**: Full functionality across desktop, tablet, and mobile devices
- **Performance Focused**: Fast loading and interaction despite large datasets
- **Accessibility**: WCAG 2.1 AA compliance

## Technology Stack

### Core Framework: React
React will serve as our core frontend framework due to:
- Component-based architecture for reusability
- Virtual DOM for performance optimization
- Strong ecosystem and community support
- Familiarity and developer efficiency

### UI Framework: Chakra UI v3
We've selected Chakra UI v3 for GovWatcher based on its significant improvements over previous versions and the following benefits:

**Key Advantages of Chakra UI v3:**
- Built-in accessibility features
- Highly customizable theming through the new "recipes" system
- Responsive design with simplified API
- Excellent documentation and growing ecosystem
- Better performance than v2 through externalized styling engine
- Integration with Ark UI components for advanced functionality
- Simplified installation (no longer requires framer-motion)

**New Features in v3 Relevant to GovWatcher:**
- Simplified component imports with Root/child pattern
- Updated props (e.g., `gap` instead of `spacing` for better CSS alignment)
- CSS animations instead of framer-motion for better performance
- Statechart-powered components for complex interactions
- More consistent design tokens across components

**Installation:**
```bash
npm install @chakra-ui/react @emotion/react
```

### Chakra Integration for Web Archive Features

For GovWatcher's specific needs, we'll leverage Chakra UI v3 in these ways:

1. **Archive Visualization**:
   - Use Chakra's Grid, Flex, and Card components for archive browsing
   - Implement the new Tabs.Root component for organizing different view types
   - Utilize the improved Modal and Drawer components for detailed content viewing

2. **Diff Visualization**:
   - Create custom diff components using Chakra's styling system
   - Implement side-by-side comparisons with Chakra Grid and responsive layout
   - Use Chakra's color tokens for highlighting additions/deletions/changes
   - Leverage Chakra's theme extension for specialized diff highlighting

3. **Integration with Diff Libraries**:
   - Integrate `react-diff-view` for rendering git-like diffs
   - Style the diff components with Chakra's theme system
   - Create custom Chakra components that wrap around the diff visualization

### State Management
- **React Context API** for global UI state
- **Redux Toolkit** for complex data management (archives, diffs, filters)
- **React Query** for server state management, caching, and data fetching

### Routing
- **React Router** for application routing
- Route-based code splitting for performance optimization

## Application Architecture

### Project Structure
We'll organize the codebase using a feature-based approach to improve maintainability and separation of concerns. This structure aligns with GovWatcher's specific needs for archive viewing and diff comparisons:

```
govwatcher-frontend/
├── public/                 # Static assets
├── src/
│   ├── assets/             # Images, icons, and other static files
│   │   ├── images/
│   │   └── icons/
│   │
│   ├── components/         # Shared UI components organized by feature
│   │   ├── common/         # Truly reusable components across features
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── Alert/
│   │   │   └── ...
│   │   │
│   │   ├── layout/         # Layout components
│   │   │   ├── Header/
│   │   │   ├── Footer/
│   │   │   ├── Sidebar/
│   │   │   └── PageContainer/
│   │   │
│   │   └── ui/             # Complex reusable UI components
│   │       ├── DataTable/
│   │       ├── SearchBar/
│   │       ├── Timeline/
│   │       └── Pagination/
│   │
│   ├── features/           # Feature-specific components and logic
│   │   ├── dashboard/      # Dashboard feature
│   │   │   ├── components/ # Dashboard-specific components
│   │   │   ├── hooks/      # Dashboard-specific hooks
│   │   │   ├── utils/      # Dashboard-specific utilities
│   │   │   └── index.js    # Feature entry point
│   │   │
│   │   ├── archive/        # Archive viewing feature
│   │   │   ├── components/ # Archive-specific components
│   │   │   │   ├── ArchiveList/
│   │   │   │   ├── ArchiveDetail/
│   │   │   │   ├── ArchiveFilter/
│   │   │   │   └── TimelineViewer/
│   │   │   ├── hooks/      # Archive-specific hooks
│   │   │   ├── utils/      # Archive-specific utilities
│   │   │   └── index.js    # Feature entry point
│   │   │
│   │   ├── diff/           # Diff comparison feature
│   │   │   ├── components/ # Diff-specific components
│   │   │   │   ├── DiffViewer/
│   │   │   │   ├── SideBySideView/
│   │   │   │   ├── UnifiedView/
│   │   │   │   ├── ChangeFilter/
│   │   │   │   └── DiffNavigation/
│   │   │   ├── hooks/      # Diff-specific hooks
│   │   │   │   ├── useDiffHighlighting.js
│   │   │   │   ├── useDiffParsing.js
│   │   │   │   └── useVersionNavigation.js
│   │   │   ├── utils/      # Diff-specific utilities
│   │   │   │   ├── diffFormatters.js
│   │   │   │   └── diffCalculation.js
│   │   │   └── index.js    # Feature entry point
│   │   │
│   │   └── social/         # Social media monitoring feature
│   │       ├── components/ # Social-specific components
│   │       ├── hooks/      # Social-specific hooks
│   │       ├── utils/      # Social-specific utilities
│   │       └── index.js    # Feature entry point
│   │
│   ├── pages/              # Page components that compose features
│   │   ├── HomePage.jsx
│   │   ├── ArchivesPage.jsx
│   │   ├── ArchiveDetailPage.jsx
│   │   ├── DiffViewPage.jsx
│   │   ├── SearchPage.jsx
│   │   └── SettingsPage.jsx
│   │
│   ├── services/           # API and external service integration
│   │   ├── api/            # API client and endpoint definitions
│   │   │   ├── client.js   # Base API client setup
│   │   │   ├── archives.js # Archive-related API calls
│   │   │   ├── diffs.js    # Diff-related API calls
│   │   │   └── social.js   # Social media API calls
│   │   │
│   │   └── storage/        # Local storage services
│   │       ├── preferences.js
│   │       └── session.js
│   │
│   ├── hooks/              # Application-wide custom hooks
│   │   ├── useAuth.js
│   │   ├── useWindowSize.js
│   │   └── useDebounce.js
│   │
│   ├── utils/              # Utility functions
│   │   ├── formatting.js   # Date, number formatting
│   │   ├── validation.js   # Input validation
│   │   └── helpers.js      # General helper functions
│   │
│   ├── store/              # State management
│   │   ├── slices/         # Redux slices
│   │   │   ├── archiveSlice.js
│   │   │   ├── diffSlice.js
│   │   │   └── uiSlice.js
│   │   ├── queries/        # React Query definitions
│   │   │   ├── archiveQueries.js
│   │   │   └── diffQueries.js
│   │   └── index.js        # Store configuration
│   │
│   ├── context/            # React Context definitions
│   │   ├── ThemeContext.jsx
│   │   └── UserPreferencesContext.jsx
│   │
│   ├── theme/              # Chakra UI theme configuration
│   │   ├── foundations/    # Base theme values
│   │   │   ├── colors.js
│   │   │   ├── fonts.js
│   │   │   └── spacing.js
│   │   ├── components/     # Component-specific theming
│   │   │   ├── button.js
│   │   │   ├── card.js
│   │   │   └── diff.js     # Diff-specific styling
│   │   └── index.js        # Theme export
│   │
│   ├── App.jsx             # Main application component
│   ├── Routes.jsx          # Route definitions
│   └── index.jsx           # Application entry point
│
├── .eslintrc.js            # ESLint configuration
├── .prettierrc             # Prettier configuration
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── vite.config.js          # Vite configuration
```

### Key Architectural Decisions

1. **Feature-Based Organization**:
   - Each major feature (dashboard, archive, diff, social) has its own directory with components, hooks, and utilities
   - This enables team members to work on features independently
   - Features can be easily found, maintained, and potentially lazy-loaded

2. **Component Structure**:
   - Each significant component gets its own directory
   - Component directories follow this pattern:
     ```
     ComponentName/
     ├── index.jsx          # Main component export
     ├── ComponentName.jsx  # Component implementation
     ├── ComponentName.test.jsx # Component tests
     └── styles.js          # Component-specific styles (if needed)
     ```
   - This keeps related files together and makes imports cleaner

3. **State Management Separation**:
   - Redux for application-wide state (e.g., user settings, filter preferences)
   - React Query for server state (API data fetching and caching)
   - React Context for theme and UI state
   - Local component state for component-specific needs

4. **Theming Strategy**:
   - Centralized theme configuration in `theme/` directory
   - Follows Chakra UI v3 conventions for theme extension
   - Special theme components for diff visualization

5. **API Service Pattern**:
   - Abstracted API calls in service modules
   - Feature-specific API functions to keep related API calls together
   - Centralized error handling and authentication logic

### Component Composition Strategy

For the core features of GovWatcher, we'll follow these composition patterns:

1. **Archive Viewing**:
   ```jsx
   // ArchiveDetailPage composition
   <PageContainer>
     <Header />
     <ArchiveDetail>
       <ArchiveMetadata />
       <TimelineViewer 
         snapshots={archiveSnapshots} 
         onSelect={handleSnapshotSelect} 
       />
       <ArchiveContent>
         <ArchiveFrame src={selectedSnapshotUrl} />
         <RelatedSocialFeed archiveId={archiveId} />
       </ArchiveContent>
     </ArchiveDetail>
   </PageContainer>
   ```

2. **Diff Viewing**:
   ```jsx
   // DiffViewPage composition
   <PageContainer>
     <Header />
     <DiffViewer>
       <DiffControls>
         <ViewTypeToggle value={viewType} onChange={setViewType} />
         <ChangeFilter filters={activeFilters} onChange={setFilters} />
       </DiffControls>
       <DiffContent>
         {viewType === 'split' ? (
           <SideBySideView oldVersion={oldVersion} newVersion={newVersion} />
         ) : (
           <UnifiedView oldVersion={oldVersion} newVersion={newVersion} />
         )}
       </DiffContent>
       <DiffNavigation 
         changes={filteredChanges} 
         onNavigate={navigateToChange} 
       />
     </DiffViewer>
   </PageContainer>
   ```

### Code Organization Best Practices

1. **Module Boundaries**:
   - Clearly define public APIs for each feature via index.js exports
   - Avoid importing internal feature components directly from other features
   - Use barrel exports for cleaner imports

2. **Component Design**:
   - Prefer smaller, focused components over large, complex ones
   - Use composition over inheritance
   - Implement prop types or TypeScript interfaces for all components

3. **Performance Considerations**:
   - Memoize expensive computations with useMemo and useCallback
   - Implement virtualization for long lists
   - Use React.memo for pure components that re-render frequently

4. **Testing Strategy**:
   - Unit tests for utility functions
   - Component tests for UI components
   - Integration tests for feature flows
   - End-to-end tests for critical user journeys

## UI Design Components

### Visualization Components
- **Timeline Viewer**: Interactive timeline using Chakra's Slider component
- **Diff Highlighter**: Custom component built with Chakra styling system
- **Heatmap**: Using Chakra Grid with dynamic color intensity
- **Network Graph**: Integration with D3.js styled with Chakra theme tokens

### Data Display Components
- **Smart Data Tables**: Using Chakra Table.Root component with custom styling
- **Virtual Lists**: Chakra Box with react-window integration for performance
- **Interactive Charts**: Recharts or Nivo with Chakra theme integration

### Navigation Components
- **Hierarchical Navigation**: Using Chakra's Accordion and Menu components
- **Breadcrumb System**: Using Chakra's Breadcrumb component
- **Search with Autocomplete**: Combining Chakra Input with a custom dropdown

## Responsive Design Strategy
- Mobile-first design approach using Chakra's responsive style props
- Breakpoint system with Chakra's built-in responsive utilities:
  - Mobile: < 480px
  - Tablet: 481px - 1024px
  - Desktop: > 1024px
- Adaptive layouts for complex visualizations
- Touch-friendly controls for mobile users

## Performance Optimization

### Initial Load Performance
- Code splitting by route
- Lazy loading of non-critical components
- Critical CSS inline loading
- Asset optimization (images, fonts)

### Runtime Performance
- Virtualized lists for long content
- Pagination for large datasets
- Memoization of expensive calculations
- Optimistic UI updates

### Data Loading Strategy
- Progressive loading of content
- Skeleton screens during loading
- Data prefetching for anticipated navigation

## Accessibility Considerations
- Leverage Chakra UI's built-in accessibility features
- Semantic HTML structure
- ARIA attributes for complex components
- Keyboard navigation support
- Screen reader compatibility
- Color contrast requirements
- Focus management

## Chakra UI Theme Configuration

We'll create a custom theme for GovWatcher that extends Chakra UI's base theme:

```jsx
// theme.js
import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
  colors: {
    brand: {
      50: '#e6f6ff',
      100: '#bae3ff',
      500: '#2b6cb0',
      900: '#1a365d',
    },
    diff: {
      added: {
        bg: '#e6ffec',
        border: '#abf2bc',
        text: '#24292f',
        bgDark: '#0f291a',
        borderDark: '#238636',
        textDark: '#adbac7',
      },
      removed: {
        bg: '#ffebe9',
        border: '#ffcecb',
        text: '#24292f',
        bgDark: '#291a1c',
        borderDark: '#f85149',
        textDark: '#adbac7',
      },
      // More diff-specific colors
    },
  },
  components: {
    Card: {
      baseStyle: {
        container: {
          boxShadow: 'sm',
          rounded: 'md',
        },
        header: {
          borderBottomWidth: '1px',
          p: 4,
        },
        body: {
          p: 4,
        },
      },
      variants: {
        archive: {
          container: {
            border: '1px solid',
            borderColor: 'gray.200',
          },
        },
        diff: {
          container: {
            border: '1px solid',
            borderColor: 'gray.300',
          },
        },
      },
    },
    // Additional component theme customizations
  },
});

export default theme;
```

## Implementation Plan

### Phase 1: Core Structure (2 weeks)
- Set up React application with TypeScript
- Implement Chakra UI v3 theming
- Implement routing structure
- Create layout components
- Establish API service layer
- Implement state management foundation

### Phase 2: Archive Viewing (2 weeks)
- Develop archive browsing interface
- Implement archive detail view
- Create timeline component
- Build archive rendering system

### Phase 3: Diff Visualization (2 weeks)
- Implement react-diff-view integration
- Create Chakra UI wrapper components
- Implement highlighting system
- Create change navigation controls
- Build export functionality

### Phase 4: Search & Discovery (1 week)
- Implement search interface
- Create filtering components
- Develop results display
- Add saved searches functionality

### Phase 5: Dashboard & Analytics (1 week)
- Create dashboard components
- Implement visualization widgets
- Add customization options
- Develop reporting features

### Phase 6: Polish & Optimization (1 week)
- Refine responsive design
- Optimize performance
- Enhance accessibility
- Add final UI polish

## Development Workflow
- Component-driven development with Storybook
- Automated testing with Jest and React Testing Library
- CI/CD pipeline for automated deployment
- Design system documentation

## Technology Decisions Checklist
- [x] UI Framework: Chakra UI v3
- [ ] Icon Library: Select from Lucide React or React Icons
- [ ] Chart/Visualization Library: Select options
- [ ] Date/Time Handling: Date-fns vs Day.js
- [ ] Diff Visualization: react-diff-view with Chakra UI styling
- [ ] State Management: Redux Toolkit + React Query
- [ ] Internationalization: if needed

## Future Enhancements
- User accounts and personalization
- Collaborative features (comments, sharing)
- Advanced analytics dashboard
- Public API with developer documentation
- Machine learning-powered change significance detection

## API Integration

### Backend API Consumption

The frontend will interact with the backend API using these patterns:

1. **API Client Configuration**:
   ```javascript
   // services/api/client.js
   import axios from 'axios';

   const apiClient = axios.create({
     baseURL: process.env.REACT_APP_API_URL || '/api',
     timeout: 30000,
     headers: {
       'Content-Type': 'application/json',
     }
   });

   // Response interceptor for error handling
   apiClient.interceptors.response.use(
     response => response,
     error => {
       // Global error handling
       return Promise.reject(error);
     }
   );

   export default apiClient;
   ```

2. **Feature-Specific API Services**:
   ```javascript
   // services/api/archives.js
   import apiClient from './client';

   export const archiveService = {
     getArchives: (params) => apiClient.get('/archives', { params }),
     getArchiveById: (id) => apiClient.get(`/archives/${id}`),
     getSnapshots: (archiveId, params) => apiClient.get(`/archives/${archiveId}/snapshots`, { params }),
     getSnapshotById: (archiveId, snapshotId) => apiClient.get(`/archives/${archiveId}/snapshots/${snapshotId}`),
   };

   // services/api/diffs.js
   import apiClient from './client';

   export const diffService = {
     getDiffs: (archiveId) => apiClient.get(`/diffs/${archiveId}`),
     getComparison: (archiveId, snapshot1Id, snapshot2Id) => 
       apiClient.get(`/diffs/${archiveId}/${snapshot1Id}/${snapshot2Id}`),
     getStatistics: (archiveId, snapshot1Id, snapshot2Id) => 
       apiClient.get(`/diffs/${archiveId}/${snapshot1Id}/${snapshot2Id}/statistics`),
   };
   ```

3. **React Query Integration**:
   ```javascript
   // hooks/queries/useArchives.js
   import { useQuery } from 'react-query';
   import { archiveService } from '../../services/api/archives';

   export const useArchives = (params, options = {}) => {
     return useQuery(
       ['archives', params],
       () => archiveService.getArchives(params),
       {
         keepPreviousData: true,
         staleTime: 5 * 60 * 1000, // 5 minutes
         ...options,
       }
     );
   };

   export const useArchiveDetail = (id, options = {}) => {
     return useQuery(
       ['archive', id],
       () => archiveService.getArchiveById(id),
       {
         enabled: !!id,
         staleTime: 5 * 60 * 1000,
         ...options,
       }
     );
   };
   ```

## Handling Archived Content

### Archived Web Page Display

The frontend will implement secure, sandboxed display of archived web content:

1. **Iframe-Based Display**:
   ```jsx
   // components/archive/ArchiveFrame/ArchiveFrame.jsx
   import { Box, useColorModeValue } from '@chakra-ui/react';
   import { useState } from 'react';

   const ArchiveFrame = ({ src, title, onLoad }) => {
     const [isLoading, setIsLoading] = useState(true);
     const borderColor = useColorModeValue('gray.200', 'gray.700');
     
     const handleLoad = () => {
       setIsLoading(false);
       if (onLoad) onLoad();
     };
     
     return (
       <Box position="relative" w="100%" h="100%" minH="500px" borderWidth="1px" borderColor={borderColor} borderRadius="md">
         {isLoading && (
           <Box position="absolute" top="0" left="0" w="100%" h="100%" bg="gray.50" 
                display="flex" alignItems="center" justifyContent="center">
             Loading archived content...
           </Box>
         )}
         <iframe 
           src={src} 
           title={title || "Archived content"} 
           width="100%" 
           height="100%" 
           onLoad={handleLoad}
           sandbox="allow-same-origin allow-scripts"
           style={{ border: 'none' }}
         />
       </Box>
     );
   };

   export default ArchiveFrame;
   ```

2. **Content Display Modes**:
   ```jsx
   // features/archive/components/ArchiveViewer/ArchiveViewer.jsx
   import { Box, Tabs, ButtonGroup, Button } from '@chakra-ui/react';
   import { useState } from 'react';
   import ArchiveFrame from '../../../../components/archive/ArchiveFrame';

   const ArchiveViewer = ({ archiveId, snapshotId, contentUrls }) => {
     const [viewMode, setViewMode] = useState('original');
     
     const getContentUrl = () => {
       switch(viewMode) {
         case 'screenshot': return contentUrls.screenshot;
         case 'pdf': return contentUrls.pdf;
         case 'original':
         default: return contentUrls.original;
       }
     };
     
     return (
       <Box>
         <ButtonGroup isAttached variant="outline" mb={4}>
           <Button 
             isActive={viewMode === 'original'} 
             onClick={() => setViewMode('original')}
           >
             Original
           </Button>
           <Button 
             isActive={viewMode === 'screenshot'} 
             onClick={() => setViewMode('screenshot')}
           >
             Screenshot
           </Button>
           <Button 
             isActive={viewMode === 'pdf'} 
             onClick={() => setViewMode('pdf')}
           >
             PDF
           </Button>
         </ButtonGroup>
         
         <ArchiveFrame 
           src={getContentUrl()}
           title={`Archive ${archiveId} - Snapshot ${snapshotId}`}
         />
       </Box>
     );
   };

   export default ArchiveViewer;
   ```

### Diff Visualization Implementation

The frontend will implement diff visualization that aligns with the backend API's diff format:

```jsx
// features/diff/components/DiffViewer/DiffViewer.jsx
import { Box, useColorModeValue } from '@chakra-ui/react';
import { Diff, Hunk, parseDiff } from 'react-diff-view';
import 'react-diff-view/style/index.css';
import { useQuery } from 'react-query';
import { diffService } from '../../../../services/api/diffs';

const DiffViewer = ({ archiveId, oldSnapshotId, newSnapshotId, viewType = 'split' }) => {
  const { data, isLoading, error } = useQuery(
    ['diff', archiveId, oldSnapshotId, newSnapshotId],
    () => diffService.getComparison(archiveId, oldSnapshotId, newSnapshotId)
  );
  
  const addedColor = useColorModeValue('diff.added.bg', 'diff.added.bgDark');
  const removedColor = useColorModeValue('diff.removed.bg', 'diff.removed.bgDark');
  
  if (isLoading) return <Box>Loading diff...</Box>;
  if (error) return <Box>Error loading diff: {error.message}</Box>;
  
  // The backend provides diff data in a format compatible with react-diff-view
  const { diffData } = data;
  
  return (
    <Box className="diff-container" sx={{
      '.diff-gutter-add': { bg: addedColor },
      '.diff-gutter-del': { bg: removedColor }
    }}>
      <Diff
        viewType={viewType}
        diffType="modify"
        hunks={diffData.hunks}
      >
        {(hunks) => hunks.map(hunk => (
          <Hunk key={hunk.content} hunk={hunk} />
        ))}
      </Diff>
    </Box>
  );
};

export default DiffViewer;
```

## Consolidated Integration Approach

To ensure proper integration with both the Backend API and Archiving system:

### System Integration Diagram

```
+-------------------+          +----------------+          +-----------------+
|                   |  API     |                |  Data    |                 |
|    React          | Calls    |    Backend     | Access   |    Archiving    |
|    Frontend       +--------->+    API         +--------->+    System       |
|                   |          |                |          |                 |
+-------------------+          +----------------+          +-----------------+
        |                              |                           |
        |                              |                           |
+-------v----------+          +--------v---------+       +---------v--------+
| Chakra UI v3     |          | Express/Node.js  |       | ArchiveBox +     |
| React Router     |          | PostgreSQL       |       | Custom Components |
| React Query      |          | Redis            |       | PostgreSQL       |
+------------------+          +------------------+       +------------------+
```

### Integration Testing Strategy

1. **Mock API Endpoints**:
   - During development, use MSW (Mock Service Worker) to simulate API responses
   - Create realistic mock data that mirrors expected production formats
   - Test edge cases and error conditions

2. **End-to-End Testing**:
   - Implement Cypress tests that validate frontend-backend integration
   - Test key user flows from archive browsing to diff viewing
   - Validate content display and visualization

3. **Component Testing**:
   - Test components with mock data matching API formats
   - Verify correct rendering and behavior with different data variations

## Deployment Considerations

### Environment Configuration

```jsx
// .env.production
REACT_APP_API_URL=https://api.govwatcher.org
REACT_APP_DEFAULT_PAGE_SIZE=20
REACT_APP_MAX_DIFF_SIZE=500000
```

### Build Optimization

1. **Bundle Size Reduction**:
   - Use code splitting to reduce initial load size
   - Implement tree-shaking for Chakra UI components
   - Optimize image assets and implement lazy loading

2. **Caching Strategy**:
   - Configure cache headers for static assets
   - Implement service worker for offline capability
   - Use versioned assets for cache busting 