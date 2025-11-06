import { Download, Trash2, CheckCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Reusable BulkActionToolbar component for bulk operations
 * 
 * @param {number} selectedCount - Number of selected items
 * @param {Function} onClearSelection - Callback to clear selection
 * @param {Array} actions - Array of action objects with { label, icon, onClick, variant, show }
 */
const BulkActionToolbar = ({ selectedCount, onClearSelection, actions = [] }) => {
  if (selectedCount === 0) return null;

  return (
    <div className="sticky top-0 z-10 bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg shadow-md mb-4 animate-in slide-in-from-top">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-blue-900">
            {selectedCount} {selectedCount === 1 ? "item" : "items"} selected
          </span>
          
          <div className="flex gap-2">
            {actions.map((action, index) => {
              // Only show action if show condition is true (default true)
              if (action.show === false) return null;
              
              const Icon = action.icon;
              
              return (
                <Button
                  key={index}
                  variant={action.variant || "default"}
                  size="sm"
                  onClick={action.onClick}
                  className="flex items-center gap-2"
                  disabled={action.disabled}
                >
                  {Icon && <Icon size={16} />}
                  {action.label}
                </Button>
              );
            })}
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onClearSelection}
          className="flex items-center gap-2"
        >
          <X size={16} />
          Clear Selection
        </Button>
      </div>
    </div>
  );
};

export default BulkActionToolbar;
