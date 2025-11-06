// src/components/Dashboard.jsx
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux'; // Import useSelector and useDispatch
import './Dashboard.css';
import { fetchDashboardData } from '../redux/slices/dashboardSlice'; // Import the async thunk
import { baseURL } from '../data';
import { isAuthenticated } from '../utils/authUtils';
import DataTable from './common/DataTable';
import { useNotification } from '../hooks/useNotification';
import { SkeletonCard, SkeletonChart } from './common/SkeletonLoader';
import CustomizableDashboard from './dashboard/CustomizableDashboard';
// LoadingSpinner not needed - DataTable handles its own loading state

// Enhanced Interactive BarChart Component
const BarChart = React.memo(({ data, title, xLabel, yLabel, tooltipLabelPrefix, dataKey, chartType = 'bar' }) => {
  if (!data || data.length === 0) {
    return <div className="chart-container no-data">No data available for {title}.</div>;
  }

  const maxCount = Math.max(...data.map(item => item.count));
  const [hoveredBar, setHoveredBar] = useState(null);
  const [selectedBar, setSelectedBar] = useState(null);
  const [showPercentage, setShowPercentage] = useState(false);
  const totalCount = data.reduce((sum, item) => sum + item.count, 0);

  const handleBarClick = (item, index) => {
    setSelectedBar(selectedBar?.index === index ? null : { ...item, index });
  };

  const togglePercentage = () => {
    setShowPercentage(!showPercentage);
  };

  return (
    <div className="chart-container card interactive-chart">
      <div className="chart-header">
        <h3 className="chart-title h4">{title}</h3>
        <div className="chart-controls">
          <button 
            className={`chart-toggle-btn ${showPercentage ? 'active' : ''}`}
            onClick={togglePercentage}
            title="Toggle between count and percentage view"
          >
            {showPercentage ? '%' : '#'}
          </button>
        </div>
      </div>
      <div className="chart-content">
        <div className="chart-bars-wrapper">
          <div className="y-axis-label text-sm font-medium">{yLabel}</div>
          <div className="chart-bars">
            {data.map((item, index) => {
              const height = showPercentage 
                ? (item.count / totalCount) * 100 
                : (item.count / maxCount) * 100;
              const percentage = ((item.count / totalCount) * 100).toFixed(1);
              const isSelected = selectedBar?.index === index;
              const isHovered = hoveredBar?.index === index;
              
              return (
                <div key={item[dataKey]} className="chart-bar-item">
                  <div
                    className={`chart-bar ${isSelected ? 'selected' : ''} ${isHovered ? 'hovered' : ''}`}
                    style={{ height: `${height}%` }}
                    onMouseEnter={() => setHoveredBar({ ...item, index })}
                    onMouseLeave={() => setHoveredBar(null)}
                    onClick={() => handleBarClick(item, index)}
                  >
                    {(isHovered || isSelected) && (
                      <div className="chart-tooltip">
                        <div className="tooltip-title">{item[dataKey]}</div>
                        <div className="tooltip-content">
                          <div>Count: {item.count}</div>
                          <div>Percentage: {percentage}%</div>
                        </div>
                      </div>
                    )}
                    {isSelected && (
                      <div className="chart-bar-value">
                        {showPercentage ? `${percentage}%` : item.count}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <div className="chart-x-axis">
          {data.map((item, index) => (
            <div 
              key={item[dataKey]} 
              className="x-axis-item"
            >
              <span 
                className="x-axis-label text-xs font-medium"
                title={item[dataKey]}
              >
                {item[dataKey].length > 6 ? `${item[dataKey].substring(0, 6)}...` : item[dataKey]}
              </span>
            </div>
          ))}
        </div>
        <div className="x-axis-title">{xLabel}</div>
      </div>
      {selectedBar && (
        <div className="chart-details">
          <h4>Details for {selectedBar[dataKey]}</h4>
          <div className="detail-stats">
            <div className="stat-item">
              <span className="stat-label">Count:</span>
              <span className="stat-value">{selectedBar.count}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Percentage:</span>
              <span className="stat-value">{((selectedBar.count / totalCount) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});


const Dashboard = () => {
  const dispatch = useDispatch();
  const notify = useNotification();
  const dashboardData = useSelector((state) => state.dashboard.dashboardData);
  const loading = useSelector((state) => state.dashboard.status === 'loading');
  const error = useSelector((state) => state.dashboard.error);
  const [useCustomizableDashboard, setUseCustomizableDashboard] = useState(true);

  // DataTable handles pagination internally, no need for local state

  useEffect(() => {
    // Only fetch dashboard data if user is properly authenticated
    const authenticated = isAuthenticated();
    
    if (authenticated && dashboardData === null && !loading && !error) {
      dispatch(fetchDashboardData());
    }
  }, [dispatch, dashboardData, loading, error]); // Dependencies to re-run effect

  if (error) {
    return <div className="error-container">Error: {error}</div>;
  }

  if (!dashboardData && loading) {
     return (
      <div className="dashboard-container is-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  if (!dashboardData) {
    return <div className="error-container">No dashboard data available.</div>;
  }

  // Use the new customizable dashboard
  if (useCustomizableDashboard) {
    return <CustomizableDashboard />;
  }

  const allRecentActivities = [
    ...(dashboardData?.resume_stats?.recent_uploads || []).map(item => ({
      id: item.id,
      name: item.file.split('/').pop(),
      detail: `Resume uploaded: ${item.file}`,
      date: new Date(item.uploaded_at).toLocaleDateString(),
      type: 'resume_upload',
      timestamp: new Date(item.uploaded_at).getTime(),
    })),
    ...(dashboardData?.candidate_stats?.recent_candidates || []).map(item => ({
      id: item.id,
      name: item.full_name || 'N/A',
      detail: `Candidate added in ${item.domain} domain with status ${item.status}`,
      date: new Date(item.created_at).toLocaleDateString(),
      type: 'new_candidate',
      timestamp: new Date(item.created_at).getTime(),
    })),
    ...(dashboardData?.job_stats?.recent_jobs || []).map(item => ({
      id: item.id,
      name: item.job_title,
      detail: `New job posted at ${item.company_name} (${item.position_level})`,
      date: new Date(item.created_at).toLocaleDateString(),
      type: 'job_posted',
      timestamp: new Date(item.created_at).getTime(),
    })),
    ...(dashboardData?.activity_data?.recent_activities || []).map(item => ({
       id: item.id,
       name: item.name,
       detail: item.detail,
       date: new Date(item.date).toLocaleDateString(),
       type: item.type,
       timestamp: new Date(item.date).getTime(),
    })),
  ].sort((a, b) => b.timestamp - a.timestamp);

  // Pagination is now handled by DataTable component

  return (
    <div className={`dashboard-container ${loading ? 'is-loading' : ''}`}>
      <main className="dashboard-main-content">
        <section className="dashboard-section card-section">
          <div className="dashboard-cards-container stagger-animation">
            {loading ? (
              <>
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
              </>
            ) : (
              <>
                <div className="dashboard-card hover-lift">
                  <h3>Total Resumes Uploaded</h3>
                  <p>{dashboardData.resume_stats.total_uploads}</p>
                </div>
                <div className="dashboard-card hover-lift">
                  <h3>Total Candidates</h3>
                  <p>{dashboardData.candidate_stats.total_candidates}</p>
                </div>
                <div className="dashboard-card hover-lift">
                  <h3>Total Jobs</h3>
                  <p>{dashboardData.job_stats.total_jobs}</p>
                </div>
                <div className="dashboard-card hover-lift">
                  <h3>Total Interviews</h3>
                  <p>{dashboardData.interview_stats.total_interviews}</p>
                </div>
              </>
            )}
          </div>
        </section>

        <section className="dashboard-section dashboard-graphs-container stagger-animation">
          <div className="dashboard-placeholder">
            <h3>Charts and Analytics</h3>
            <p>Interactive charts and analytics are now available in the customizable dashboard above.</p>
            <button 
              className="btn btn-primary"
              onClick={() => setUseCustomizableDashboard(true)}
            >
              View Customizable Dashboard
            </button>
          </div>
        </section>

        <section className="dashboard-recent-activity">
          <DataTable
            title="Recent Activities"
            columns={[
              {
                field: "name",
                header: "Name/Subject",
                width: "25%",
              },
              {
                field: "detail",
                header: "Detail",
                width: "35%",
              },
              {
                field: "date",
                header: "Date",
                width: "20%",
              },
              {
                field: "type",
                header: "Category",
                width: "20%",
                render: (value) => (
                  <span className="status-cell" data-status={value?.toLowerCase()}>
                    {value.replace(/_/g, ' ')}
                  </span>
                ),
              },
            ]}
            data={allRecentActivities || []}
            loading={loading}
            actions={[]} // No actions for activities
            showRefresh={true}
            onRefresh={async () => {
              try {
                await dispatch(fetchDashboardData()).unwrap();
                notify.success("Dashboard data refreshed successfully!");
              } catch (error) {
                notify.error("Failed to refresh dashboard data. Please try again.");
              }
            }}
            showActions={false}
            defaultPageSize={10}
            pageSizeOptions={[10, 20, 50]}
          />
        </section>
      </main>
    </div>
  );
};

export default React.memo(Dashboard);
