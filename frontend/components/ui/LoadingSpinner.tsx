/**
 * Loading Spinner Component
 */

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingSpinner({ size = 'md' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };
  
  return (
    <div className="flex justify-center items-center">
      <div
        className={`
          ${sizeClasses[size]}
          border-4 border-gray-200 border-t-blue-600
          rounded-full animate-spin
        `}
      />
    </div>
  );
}
