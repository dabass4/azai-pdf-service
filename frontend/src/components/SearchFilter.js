import { useState, useEffect } from "react";
import { Search, Filter, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

/**
 * Reusable SearchFilter component for instant search with debouncing
 * 
 * @param {Function} onSearch - Callback function when search/filter changes
 * @param {Object} filters - Configuration object for available filters
 * @param {string} placeholder - Search input placeholder
 */
const SearchFilter = ({ onSearch, filters = {}, placeholder = "Search..." }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterValues, setFilterValues] = useState({});
  const [showFilters, setShowFilters] = useState(false);

  // Debounced search - triggers 300ms after user stops typing
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch({ search: searchTerm, ...filterValues });
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm, filterValues]);

  const handleFilterChange = (filterName, value) => {
    setFilterValues(prev => ({
      ...prev,
      [filterName]: value === "all" ? undefined : value
    }));
  };

  const clearFilters = () => {
    setSearchTerm("");
    setFilterValues({});
    onSearch({ search: "", ...{} });
  };

  const hasActiveFilters = searchTerm || Object.keys(filterValues).some(key => filterValues[key]);

  return (
    <div className="space-y-3">
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
          <Input
            type="text"
            placeholder={placeholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-10"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm("")}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={18} />
            </button>
          )}
        </div>
        
        {Object.keys(filters).length > 0 && (
          <Button
            variant={showFilters ? "default" : "outline"}
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter size={18} />
            Filters
          </Button>
        )}

        {hasActiveFilters && (
          <Button
            variant="ghost"
            onClick={clearFilters}
            className="flex items-center gap-2"
          >
            <X size={18} />
            Clear
          </Button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && Object.keys(filters).length > 0 && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {Object.entries(filters).map(([filterName, filterConfig]) => (
              <div key={filterName}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {filterConfig.label}
                </label>
                
                {filterConfig.type === "select" && (
                  <Select
                    value={filterValues[filterName] || "all"}
                    onValueChange={(value) => handleFilterChange(filterName, value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder={filterConfig.placeholder || "Select..."} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      {filterConfig.options.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                {filterConfig.type === "date" && (
                  <Input
                    type="date"
                    value={filterValues[filterName] || ""}
                    onChange={(e) => handleFilterChange(filterName, e.target.value)}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchFilter;
