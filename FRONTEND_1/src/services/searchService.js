// src/services/searchService.js
import { baseURL } from '../data';

/**
 * Global Search Service
 * Provides comprehensive search across all application data
 */
class SearchService {
  constructor() {
    this.searchableData = {
      candidates: [],
      jobs: [],
      hiringAgencies: [],
      companies: [],
      recruiters: [],
      interviewSlots: [],
    };
    this.lastFetchTime = {};
    this.cacheDuration = 5 * 60 * 1000; // 5 minutes cache
  }

  /**
   * Update searchable data for a specific type
   */
  updateData(type, data) {
    this.searchableData[type] = Array.isArray(data) ? data : [];
    this.lastFetchTime[type] = Date.now();
  }

  /**
   * Check if data needs refresh
   */
  needsRefresh(type) {
    const lastFetch = this.lastFetchTime[type];
    return !lastFetch || (Date.now() - lastFetch) > this.cacheDuration;
  }

  /**
   * Fetch fresh data for search if needed
   */
  async fetchDataIfNeeded(type, authToken, forceRefresh = false) {
    if (!forceRefresh && !this.needsRefresh(type)) return;

    try {
      let endpoint = '';
      switch (type) {
        case 'candidates':
          endpoint = '/api/candidates/';
          break;
        case 'jobs':
          endpoint = '/api/jobs/';
          break;
        case 'hiringAgencies':
          endpoint = '/api/hiring_agency/';
          break;
        case 'companies':
          endpoint = '/api/companies/';
          break;
        case 'recruiters':
          endpoint = '/api/companies/recruiters/';
          break;
        case 'interviewSlots':
          endpoint = '/api/interviews/slots/';
          break;
        case 'domains':
          endpoint = '/api/jobs/domains/';
          break;
        case 'interviews':
          endpoint = '/api/interviews/';
          break;
        default:
          return;
      }

      const response = await fetch(`${baseURL}${endpoint}`, {
        headers: {
          'Authorization': `Token ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        this.updateData(type, Array.isArray(data) ? data : data.results || []);
      }
    } catch (error) {
      console.error(`Error fetching ${type} for search:`, error);
    }
  }

  /**
   * Search across all data types
   */
  search(query, options = {}) {
    if (!query || query.length < 2) return [];

    const {
      limit = 50,
      includeTypes = ['candidates', 'jobs', 'domains', 'hiringAgencies', 'companies', 'recruiters', 'interviewSlots', 'interviews'],
      sortByRelevance = true,
    } = options;

    console.log('Search query:', query);
    console.log('Available data:', {
      candidates: this.searchableData.candidates.length,
      jobs: this.searchableData.jobs.length,
      domains: this.searchableData.domains.length,
      hiringAgencies: this.searchableData.hiringAgencies.length,
      companies: this.searchableData.companies.length,
      recruiters: this.searchableData.recruiters.length,
      interviewSlots: this.searchableData.interviewSlots.length,
      interviews: this.searchableData.interviews.length,
    });

    const results = [];
    const lowerQuery = query.toLowerCase();

    // Search candidates
    if (includeTypes.includes('candidates')) {
      this.searchableData.candidates.forEach((candidate, index) => {
        // Debug first candidate to see field structure
        if (index === 0) {
          console.log('Sample candidate data:', candidate);
          console.log('Candidate fields:', Object.keys(candidate));
        }
        
        const candidateName = candidate.full_name || candidate.name || 
                             (candidate.first_name && candidate.last_name ? 
                              `${candidate.first_name} ${candidate.last_name}` : 
                              candidate.username || null);
        
        // Search ALL fields in candidate object
        const searchableText = Object.values(candidate)
          .filter(value => value !== null && value !== undefined && value !== '')
          .map(value => String(value))
          .join(' ')
          .toLowerCase();

        if (searchableText.includes(lowerQuery)) {
          console.log('Found candidate match:', candidateName, 'Type: Candidates');
          results.push({
            id: candidate.id,
            type: 'Candidates',
            title: candidateName || 'Unknown Candidate',
            subtitle: `${candidate.job_title || candidate.jobTitle || 'No Job'} • ${candidate.domain_name || candidate.domain || 'No Domain'}`,
            description: `${candidate.email || ''} • ${candidate.current_status || candidate.status || 'No Status'}`,
            path: '/candidates',
            detailPath: `/candidates/${candidate.id}`,
            data: candidate,
            relevance: this.calculateRelevance(searchableText, lowerQuery),
          });
        }
      });
    }

    // Search jobs
    if (includeTypes.includes('jobs')) {
      this.searchableData.jobs.forEach(job => {
        // Search ALL fields in job object
        const searchableText = Object.values(job)
          .filter(value => value !== null && value !== undefined && value !== '')
          .map(value => String(value))
          .join(' ')
          .toLowerCase();

        if (searchableText.includes(lowerQuery)) {
          console.log('Found job match:', job.job_title, 'Type: Jobs');
          results.push({
            id: job.id,
            type: 'Jobs',
            title: job.job_title || 'Unknown Job',
            subtitle: `${job.company_name || 'No Company'} • ${job.domain_name || 'No Domain'}`,
            description: `${job.position_level || ''} • ${job.spoc_email || ''}`,
            path: '/jobs',
            detailPath: '/jobs',
            data: job,
            relevance: this.calculateRelevance(searchableText, lowerQuery),
          });
        }
      });
    }

    // Search hiring agencies
    if (includeTypes.includes('hiringAgencies')) {
      this.searchableData.hiringAgencies.forEach(agency => {
        // Search ALL fields in agency object
        const searchableText = Object.values(agency)
          .filter(value => value !== null && value !== undefined && value !== '')
          .map(value => String(value))
          .join(' ')
          .toLowerCase();

        if (searchableText.includes(lowerQuery)) {
          // Determine the correct tab based on user role
          let tabName = 'Hiring Agency'; // default
          if (agency.role) {
            const role = agency.role.toLowerCase();
            if (role === 'recruiter') tabName = 'Recruiter';
            else if (role === 'company') tabName = 'Company';
            else if (role === 'admin') tabName = 'Admin';
            else if (role === 'hiring_agency') tabName = 'Hiring Agency';
          }

          results.push({
            id: agency.id,
            type: 'Hiring Agencies',
            title: `${agency.first_name || ''} ${agency.last_name || ''}`.trim() || 'Unknown User',
            subtitle: `${agency.role || 'No Role'} • ${agency.company_name || 'No Company'}`,
            description: agency.email || '',
            path: '/hiring-agencies',
            detailPath: '/hiring-agencies',
            tab: tabName,
            data: agency,
            relevance: this.calculateRelevance(searchableText, lowerQuery),
          });
        }
      });
    }

    // Search recruiters
    if (includeTypes.includes('recruiters')) {
      this.searchableData.recruiters.forEach(recruiter => {
        // Search ALL fields in recruiter object
        const searchableText = Object.values(recruiter)
          .filter(value => value !== null && value !== undefined && value !== '')
          .map(value => String(value))
          .join(' ')
          .toLowerCase();

        if (searchableText.includes(lowerQuery)) {
          console.log('Found recruiter match:', recruiter.full_name, 'Type: Recruiters');
          const recruiterName = recruiter.full_name || 
                               (recruiter.first_name && recruiter.last_name ? 
                                `${recruiter.first_name} ${recruiter.last_name}` : 
                                recruiter.name || recruiter.username || 'Unknown Recruiter');
          
          results.push({
            id: recruiter.id,
            type: 'Recruiters',
            title: recruiterName,
            subtitle: `${recruiter.role || 'Recruiter'} • ${recruiter.company_name || 'No Company'}`,
            description: recruiter.email || '',
            path: '/hiring-agencies',
            detailPath: '/hiring-agencies',
            tab: 'Recruiter',
            data: recruiter,
            relevance: this.calculateRelevance(searchableText, lowerQuery),
          });
        }
      });
    }

    // Search companies
    if (includeTypes.includes('companies')) {
      this.searchableData.companies.forEach(company => {
        // Search ALL fields in company object
        const searchableText = Object.values(company)
          .filter(value => value !== null && value !== undefined && value !== '')
          .map(value => String(value))
          .join(' ')
          .toLowerCase();

        if (searchableText.includes(lowerQuery)) {
          results.push({
            id: company.id,
            type: 'Companies',
            title: company.name || 'Unknown Company',
            subtitle: company.domain || 'No Domain',
            description: company.email || '',
            path: '/hiring-agencies',
            detailPath: '/hiring-agencies',
            tab: 'Company',
            data: company,
            relevance: this.calculateRelevance(searchableText, lowerQuery),
          });
        }
      });
    }

    // Search interview slots
    if (includeTypes.includes('interviewSlots')) {
      this.searchableData.interviewSlots.forEach(slot => {
        // Search ALL fields in interview slot object
        const searchableText = Object.values(slot)
          .filter(value => value !== null && value !== undefined && value !== '')
          .map(value => String(value))
          .join(' ')
          .toLowerCase();

        if (searchableText.includes(lowerQuery)) {
          console.log('Found interview slot match:', slot.job_title, 'Type: Interview Scheduler');
          results.push({
            id: slot.id,
            type: 'Interview Scheduler',
            title: `${slot.job_title || 'Interview Slot'} - ${slot.interview_date || ''}`,
            subtitle: `${slot.company_name || 'No Company'} • ${slot.ai_interview_type || 'No Type'}`,
            description: `${slot.status || ''} • ${slot.start_time || ''}-${slot.end_time || ''}`,
            path: '/ai-interview-scheduler',
            detailPath: '/ai-interview-scheduler',
            data: slot,
            relevance: this.calculateRelevance(searchableText, lowerQuery),
          });
        }
      });
    }

    // Sort by relevance if requested
    if (sortByRelevance) {
      results.sort((a, b) => b.relevance - a.relevance);
    }

    console.log('Final search results:', results.map(r => ({ title: r.title, type: r.type })));
    return results.slice(0, limit);
  }

  /**
   * Calculate search relevance score
   */
  calculateRelevance(text, query) {
    let score = 0;
    const words = query.split(' ').filter(word => word.length > 0);
    
    words.forEach(word => {
      const index = text.indexOf(word);
      if (index === 0) score += 10; // Starts with query
      else if (index > 0) score += 5; // Contains query
      
      // Bonus for exact word matches
      const wordRegex = new RegExp(`\\b${word}\\b`, 'i');
      if (wordRegex.test(text)) score += 3;
    });

    return score;
  }

  /**
   * Get search suggestions based on popular searches
   */
  getSearchSuggestions(query = '', limit = 5) {
    const suggestions = [
      'candidates',
      'jobs',
      'interview slots',
      'hiring agencies',
      'companies',
      'scheduled interviews',
      'completed evaluations',
      'available slots',
    ];

    if (!query) return suggestions.slice(0, limit);

    return suggestions
      .filter(suggestion => suggestion.toLowerCase().includes(query.toLowerCase()))
      .slice(0, limit);
  }
}

// Export singleton instance
export const searchService = new SearchService();
export default searchService;
