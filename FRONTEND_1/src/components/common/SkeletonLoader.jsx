import React from 'react';
import './SkeletonLoader.css';

const SkeletonLoader = ({ 
  type = 'text', 
  width = '100%', 
  height = '1rem', 
  lines = 1, 
  className = '',
  animated = true 
}) => {
  const getSkeletonClass = () => {
    const baseClass = `skeleton-loader skeleton-${type}`;
    const animationClass = animated ? 'skeleton-animated' : '';
    return `${baseClass} ${animationClass} ${className}`.trim();
  };

  const renderSkeleton = () => {
    switch (type) {
      case 'text':
        return Array.from({ length: lines }, (_, index) => (
          <div
            key={index}
            className={getSkeletonClass()}
            style={{
              width: index === lines - 1 ? '75%' : width,
              height,
              marginBottom: index < lines - 1 ? '0.5rem' : '0'
            }}
          />
        ));

      case 'card':
        return (
          <div className="skeleton-card">
            <div className={`${getSkeletonClass()}`} style={{ height: '200px', marginBottom: '1rem' }} />
            <div className={`${getSkeletonClass()}`} style={{ height: '1.5rem', width: '80%', marginBottom: '0.5rem' }} />
            <div className={`${getSkeletonClass()}`} style={{ height: '1rem', width: '60%', marginBottom: '0.5rem' }} />
            <div className={`${getSkeletonClass()}`} style={{ height: '1rem', width: '40%' }} />
          </div>
        );

      case 'table':
        return (
          <div className="skeleton-table">
            <div className="skeleton-table-header">
              {Array.from({ length: 4 }, (_, index) => (
                <div
                  key={index}
                  className={getSkeletonClass()}
                  style={{ height: '2rem', width: `${100 / 4}%` }}
                />
              ))}
            </div>
            {Array.from({ length: 5 }, (_, rowIndex) => (
              <div key={rowIndex} className="skeleton-table-row">
                {Array.from({ length: 4 }, (_, colIndex) => (
                  <div
                    key={colIndex}
                    className={getSkeletonClass()}
                    style={{ 
                      height: '3rem', 
                      width: `${100 / 4}%`,
                      marginRight: colIndex < 3 ? '1rem' : '0'
                    }}
                  />
                ))}
              </div>
            ))}
          </div>
        );

      case 'chart':
        return (
          <div className="skeleton-chart">
            <div className={`${getSkeletonClass()}`} style={{ height: '1.5rem', width: '60%', marginBottom: '1rem' }} />
            <div className="skeleton-chart-bars">
              {Array.from({ length: 6 }, (_, index) => (
                <div
                  key={index}
                  className={`${getSkeletonClass()}`}
                  style={{ 
                    height: `${Math.random() * 60 + 20}%`,
                    width: '12%',
                    marginRight: index < 5 ? '1%' : '0'
                  }}
                />
              ))}
            </div>
            <div className="skeleton-chart-labels">
              {Array.from({ length: 6 }, (_, index) => (
                <div
                  key={index}
                  className={`${getSkeletonClass()}`}
                  style={{ height: '0.8rem', width: '12%', marginRight: index < 5 ? '1%' : '0' }}
                />
              ))}
            </div>
          </div>
        );

      case 'form':
        return (
          <div className="skeleton-form">
            {Array.from({ length: 4 }, (_, index) => (
              <div key={index} className="skeleton-form-group">
                <div className={`${getSkeletonClass()}`} style={{ height: '1rem', width: '30%', marginBottom: '0.5rem' }} />
                <div className={`${getSkeletonClass()}`} style={{ height: '2.5rem', width: '100%' }} />
              </div>
            ))}
            <div className="skeleton-form-actions">
              <div className={`${getSkeletonClass()}`} style={{ height: '2.5rem', width: '120px' }} />
            </div>
          </div>
        );

      case 'avatar':
        return (
          <div className="skeleton-avatar">
            <div className={`${getSkeletonClass()}`} style={{ width: height, height, borderRadius: '50%' }} />
          </div>
        );

      case 'button':
        return (
          <div className={`${getSkeletonClass()}`} style={{ height: '2.5rem', width, borderRadius: '6px' }} />
        );

      case 'image':
        return (
          <div className={`${getSkeletonClass()}`} style={{ width, height, borderRadius: '8px' }} />
        );

      default:
        return (
          <div
            className={getSkeletonClass()}
            style={{ width, height }}
          />
        );
    }
  };

  return <div className="skeleton-container">{renderSkeleton()}</div>;
};

// Predefined skeleton components for common use cases
export const SkeletonCard = (props) => <SkeletonLoader type="card" {...props} />;
export const SkeletonTable = (props) => <SkeletonLoader type="table" {...props} />;
export const SkeletonChart = (props) => <SkeletonLoader type="chart" {...props} />;
export const SkeletonForm = (props) => <SkeletonLoader type="form" {...props} />;
export const SkeletonText = (props) => <SkeletonLoader type="text" {...props} />;
export const SkeletonAvatar = (props) => <SkeletonLoader type="avatar" {...props} />;
export const SkeletonButton = (props) => <SkeletonLoader type="button" {...props} />;
export const SkeletonImage = (props) => <SkeletonLoader type="image" {...props} />;

export default SkeletonLoader;
