// src/components/GlobalSearch.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiX, FiClock, FiArrowRight } from 'react-icons/fi';
import { 
  setSearchTerm, 
  selectSearchResult, 
  clearSearch,
  performGlobalSearch,
  selectSearchResults,
  selectIsSearching,
  selectSearchHistory,
  addToSearchHistory,
} from '../redux/slices/searchSlice';
import { searchService } from '../services/searchService';
import './GlobalSearch.css';

const GlobalSearch = ({ isMobile = false, onResultSelect }) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  const searchTerm = useSelector(state => state.search.searchTerm);
  const searchResults = useSelector(selectSearchResults);
  const isSearching = useSelector(selectIsSearching);
  const searchHistory = useSelector(selectSearchHistory);
  
  const [localSearchTerm, setLocalSearchTerm] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  
  const searchInputRef = useRef(null);
  const dropdownRef = useRef(null);
  const searchTimeout = useRef(null);

  // Sync with Redux search term
  useEffect(() => {
    setLocalSearchTerm(searchTerm);
  }, [searchTerm]);

  // Handle search input changes
  const handleSearchChange = useCallback((e) => {
    const value = e.target.value;
    setLocalSearchTerm(value);
    dispatch(setSearchTerm(value));
    setSelectedIndex(-1);

    // Clear previous timeout
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    if (value.length >= 2) {
      setShowDropdown(true);
      
      // Debounce search
      searchTimeout.current = setTimeout(() => {
        dispatch(performGlobalSearch({ 
          query: value, 
          options: { limit: 10 } 
        }));
      }, 300);
      
      // Get suggestions
      const searchSuggestions = searchService.getSearchSuggestions(value, 3);
      setSuggestions(searchSuggestions);
    } else {
      setShowDropdown(false);
      setSuggestions([]);
    }
  }, [dispatch]);

  // Handle result selection
  const handleResultSelect = useCallback((result, fromHistory = false) => {
    dispatch(selectSearchResult(result));
    
    if (!fromHistory) {
      dispatch(addToSearchHistory(result));
    }
    
    // Navigate to the component
    navigate(`/${result.path}`);
    
    // Close dropdown
    setShowDropdown(false);
    
    // Call callback if provided (for mobile modal close)
    if (onResultSelect) {
      onResultSelect(result);
    }
  }, [dispatch, navigate, onResultSelect]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((e) => {
    if (!showDropdown) return;
    
    const totalItems = searchResults.length + suggestions.length + searchHistory.length;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % totalItems);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev <= 0 ? totalItems - 1 : prev - 1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          const allItems = [...searchResults, ...suggestions.map(s => ({ 
            type: 'suggestion', 
            title: s, 
            path: getPathForSuggestion(s) 
          })), ...searchHistory];
          if (allItems[selectedIndex]) {
            if (allItems[selectedIndex].type === 'suggestion') {
              setLocalSearchTerm(allItems[selectedIndex].title);
              dispatch(setSearchTerm(allItems[selectedIndex].title));
            } else {
              handleResultSelect(allItems[selectedIndex]);
            }
          }
        } else if (searchResults.length > 0) {
          handleResultSelect(searchResults[0]);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  }, [showDropdown, selectedIndex, searchResults, suggestions, searchHistory, handleResultSelect, dispatch]);

  // Get path for suggestion
  const getPathForSuggestion = (suggestion) => {
    const pathMap = {
      'candidates': 'candidates',
      'jobs': 'jobs',
      'interview slots': 'ai-interview-scheduler',
      'hiring agencies': 'hiring-agencies',
      'companies': 'hiring-agencies',
      'scheduled interviews': 'candidates',
      'completed evaluations': 'candidates',
      'available slots': 'ai-interview-scheduler',
    };
    return pathMap[suggestion] || 'dashboard';
  };

  // Handle clear search
  const handleClearSearch = useCallback(() => {
    setLocalSearchTerm('');
    dispatch(clearSearch());
    setShowDropdown(false);
    setSelectedIndex(-1);
    searchInputRef.current?.focus();
  }, [dispatch]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target) &&
        searchInputRef.current &&
        !searchInputRef.current.contains(event.target)
      ) {
        setShowDropdown(false);
        setSelectedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Render search result item
  const renderSearchResult = (result, index, isHistory = false) => {
    const isSelected = selectedIndex === index;
    
    return (
      <div
        key={`${result.type}-${result.id}-${index}`}
        className={`search-result-item ${isSelected ? 'selected' : ''} ${isHistory ? 'history-item' : ''}`}
        onClick={() => handleResultSelect(result, isHistory)}
      >
        <div className="search-result-content">
          <div className="search-result-title">
            {isHistory && <FiClock className="history-icon" />}
            {result.title}
            <span className="search-result-type">{result.type}</span>
          </div>
          {result.subtitle && (
            <div className="search-result-subtitle">{result.subtitle}</div>
          )}
          {result.description && (
            <div className="search-result-description">{result.description}</div>
          )}
        </div>
        <FiArrowRight className="search-result-arrow" />
      </div>
    );
  };

  return (
    <div className={`global-search ${isMobile ? 'mobile' : 'desktop'}`} ref={dropdownRef}>
      <div className="search-input-container">
        <FiSearch className="search-icon" />
        <input
          ref={searchInputRef}
          type="text"
          placeholder="Search candidates, jobs, users..."
          value={localSearchTerm}
          onChange={handleSearchChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (localSearchTerm.length >= 2 || searchHistory.length > 0) {
              setShowDropdown(true);
            }
          }}
          className="search-input"
        />
        {localSearchTerm && (
          <button
            className="clear-search-btn"
            onClick={handleClearSearch}
            title="Clear search"
          >
            <FiX />
          </button>
        )}
        {isSearching && (
          <div className="search-loading">
            <div className="search-spinner"></div>
          </div>
        )}
      </div>

      {showDropdown && (
        <div className="search-dropdown">
          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="search-section">
              <div className="search-section-header">Search Results</div>
              {searchResults.map((result, index) => renderSearchResult(result, index))}
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && localSearchTerm && (
            <div className="search-section">
              <div className="search-section-header">Suggestions</div>
              {suggestions.map((suggestion, index) => (
                <div
                  key={suggestion}
                  className={`search-suggestion-item ${
                    selectedIndex === searchResults.length + index ? 'selected' : ''
                  }`}
                  onClick={() => {
                    setLocalSearchTerm(suggestion);
                    dispatch(setSearchTerm(suggestion));
                    dispatch(performGlobalSearch({ 
                      query: suggestion, 
                      options: { limit: 10 } 
                    }));
                  }}
                >
                  <FiSearch className="suggestion-icon" />
                  {suggestion}
                </div>
              ))}
            </div>
          )}

          {/* Search History */}
          {searchHistory.length > 0 && !localSearchTerm && (
            <div className="search-section">
              <div className="search-section-header">Recent Searches</div>
              {searchHistory.slice(0, 5).map((result, index) => 
                renderSearchResult(result, searchResults.length + suggestions.length + index, true)
              )}
            </div>
          )}

          {/* No Results */}
          {localSearchTerm && searchResults.length === 0 && !isSearching && (
            <div className="search-no-results">
              <div className="no-results-icon">🔍</div>
              <div className="no-results-text">No results found for "{localSearchTerm}"</div>
              <div className="no-results-suggestion">Try searching for candidates, jobs, or users</div>
            </div>
          )}

          {/* Empty State */}
          {!localSearchTerm && searchHistory.length === 0 && (
            <div className="search-empty-state">
              <div className="empty-state-icon">🔍</div>
              <div className="empty-state-text">Search across all your data</div>
              <div className="empty-state-suggestion">Try: candidate names, job titles, company names</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GlobalSearch;




