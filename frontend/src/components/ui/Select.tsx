import { SelectHTMLAttributes, forwardRef } from 'react';

import { cn } from '@/lib/cn';

interface Option {
  value: string | number;
  label: string;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  label?: string;
  options: Option[];
  placeholder?: string;
}

const selectClasses =
  'w-full px-3 py-2.5 rounded-lg border border-gray-200 text-gray-900 bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all text-sm';

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, id, options, placeholder, className, ...rest }, ref) => {
    const selectId = id ?? rest.name;
    return (
      <div>
        {label && (
          <label
            htmlFor={selectId}
            className="block text-xs font-medium text-gray-500 mb-1.5"
          >
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(selectClasses, className)}
          {...rest}
        >
          {placeholder !== undefined && <option value="">{placeholder}</option>}
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>
    );
  },
);
Select.displayName = 'Select';
