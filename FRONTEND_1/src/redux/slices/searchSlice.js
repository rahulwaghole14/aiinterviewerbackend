// src/redux/slices/searchSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { searchService } from '../../services/searchService';

// Async thunk for performing global search
export const performGlobalSearch = createAsyncThunk(
  'search/performGlobalSearch',
  async ({ query, options }, { getState }) => {
    const { user } = getState();
    const authToken = localStorage.getItem('authToken');
    
    if (!authToken) {
      throw new Error('Authentication required for search');
    }

    // Update search service with latest data if needed
    await Promise.all([
      searchService.fetchDataIfNeeded('candidates', authToken),
      searchService.fetchDataIfNeeded('jobs', authToken),
      searchService.fetchDataIfNeeded('hiringAgencies', authToken),
      searchService.fetchDataIfNeeded('companies', authToken),
      searchService.fetchDataIfNeeded('interviewSlots', authToken),
    ]);

    // Perform the search
    const results = searchService.search(query, options);
    
    return {
      query,
      results,
      timestamp: Date.now(),
    };
  }
);

const initialState = {
  searchTerm: '',
  results: [],
  suggestions: [],
  isSearching: false,
  lastSearchQuery: '',
  selectedResult: null,
  searchHistory: [],
  isSearchModalOpen: false,
  highlightedItems: [], // Items to highlight in tables
  error: null,
};

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setSearchTerm: (state, action) => {
      state.searchTerm = action.payload;
      
      // Clear results if search term is empty
      if (!action.payload) {
        state.results = [];
        state.highlightedItems = [];
        state.selectedResult = null;
      }
    },

    setSearchResults: (state, action) => {
      state.results = action.payload;
    },

    setSearchSuggestions: (state, action) => {
      state.suggestions = action.payload;
    },

    selectSearchResult: (state, action) => {
      const result = action.payload;
      state.selectedResult = result;
      state.highlightedItems = [result.id];
      
      // Add to search history (keep last 10)
      const newHistory = [result, ...state.searchHistory.filter(item => item.id !== result.id)];
      state.searchHistory = newHistory.slice(0, 10);
    },

    clearSearchSelection: (state) => {
      state.selectedResult = null;
      state.highlightedItems = [];
    },

    setSearchModalOpen: (state, action) => {
      state.isSearchModalOpen = action.payload;
      
      // Clear search when closing modal
      if (!action.payload) {
        state.searchTerm = '';
        state.results = [];
        state.highlightedItems = [];
        state.selectedResult = null;
      }
    },

    addToSearchHistory: (state, action) => {
      const item = action.payload;
      const newHistory = [item, ...state.searchHistory.filter(h => h.id !== item.id)];
      state.searchHistory = newHistory.slice(0, 10);
    },

    clearSearchHistory: (state) => {
      state.searchHistory = [];
    },

    setHighlightedItems: (state, action) => {
      state.highlightedItems = action.payload;
    },

    clearSearch: (state) => {
      state.searchTerm = '';
      state.results = [];
      state.suggestions = [];
      state.selectedResult = null;
      state.highlightedItems = [];
      state.lastSearchQuery = '';
      state.error = null;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(performGlobalSearch.pending, (state) => {
        state.isSearching = true;
        state.error = null;
      })
      .addCase(performGlobalSearch.fulfilled, (state, action) => {
        state.isSearching = false;
        state.results = action.payload.results;
        state.lastSearchQuery = action.payload.query;
        state.error = null;
      })
      .addCase(performGlobalSearch.rejected, (state, action) => {
        state.isSearching = false;
        state.error = action.error.message || 'Search failed';
        state.results = [];
      });
  },
});

export const {
  setSearchTerm,
  setSearchResults,
  setSearchSuggestions,
  selectSearchResult,
  clearSearchSelection,
  setSearchModalOpen,
  addToSearchHistory,
  clearSearchHistory,
  setHighlightedItems,
  clearSearch,
} = searchSlice.actions;

// Selectors
export const selectSearchTerm = (state) => state.search.searchTerm;
export const selectSearchResults = (state) => state.search.results;
export const selectSearchSuggestions = (state) => state.search.suggestions;
export const selectIsSearching = (state) => state.search.isSearching;
export const selectSelectedResult = (state) => state.search.selectedResult;
export const selectSearchHistory = (state) => state.search.searchHistory;
export const selectHighlightedItems = (state) => state.search.highlightedItems;
export const selectIsSearchModalOpen = (state) => state.search.isSearchModalOpen;

export default searchSlice.reducer;




