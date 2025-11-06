// src/redux/reducers/index.js

import { combineReducers } from 'redux';
import searchReducer from './searchReducer';

const rootReducer = combineReducers({
  search: searchReducer,
  // Add other reducers here if you create them later
});

export default rootReducer;
