import { InputHTMLAttributes, forwardRef } from 'react';

import { cn } from '@/lib/cn';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

const inputClasses =
  'w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 placeholder-gray-400 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm';

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, id, className, ...rest }, ref) => {
    const inputId = id ?? rest.name;
    return (
      <div>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-medium text-gray-500 mb-1.5"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(inputClasses, className)}
          {...rest}
        />
      </div>
    );
  },
);
Input.displayName = 'Input';

export { inputClasses };
