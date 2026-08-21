import { useState } from "react";
import { Search, ChevronDown, ChevronUp, Filter } from "lucide-react";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";

export default function DataTable({ 
  data, 
  columns, 
  onRowClick,
  searchable = true,
  filterable = true 
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortColumn, setSortColumn] = useState(null);
  const [sortDirection, setSortDirection] = useState("asc");
  const [filterColumn, setFilterColumn] = useState(null);
  const [filterValue, setFilterValue] = useState("");

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  };

  const filteredAndSortedData = data
    .filter((row) => {
      // Search filter
      if (searchQuery) {
        const searchLower = searchQuery.toLowerCase();
        return Object.values(row).some(
          (value) =>
            value &&
            value.toString().toLowerCase().includes(searchLower)
        );
      }
      return true;
    })
    .filter((row) => {
      // Column filter
      if (filterColumn && filterValue) {
        return row[filterColumn]?.toString().toLowerCase() === filterValue.toLowerCase();
      }
      return true;
    })
    .sort((a, b) => {
      if (!sortColumn) return 0;
      const aVal = a[sortColumn] || "";
      const bVal = b[sortColumn] || "";
      
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDirection === "asc" ? aVal - bVal : bVal - aVal;
      }
      
      return sortDirection === "asc"
        ? aVal.toString().localeCompare(bVal.toString())
        : bVal.toString().localeCompare(aVal.toString());
    });

  const uniqueColumnValues = filterable ? columns.reduce((acc, col) => {
    if (col.filterable) {
      acc[col.key] = [...new Set(data.map(row => row[col.key]))].filter(Boolean);
    }
    return acc;
  }, {}) : {};

  return (
    <div className="space-y-4">
      {(searchable || Object.keys(uniqueColumnValues).length > 0) && (
        <div className="flex flex-wrap gap-3">
          {searchable && (
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted" />
              <Input
                placeholder="Search records..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          )}
          
          {Object.keys(uniqueColumnValues).map((colKey) => (
            <select
              key={colKey}
              value={filterColumn === colKey ? filterValue : ""}
              onChange={(e) => {
                if (e.target.value) {
                  setFilterColumn(colKey);
                  setFilterValue(e.target.value);
                } else {
                  setFilterColumn(null);
                  setFilterValue("");
                }
              }}
              className="px-3 py-2 border border-line rounded-lg text-sm bg-white"
            >
              <option value="">Filter by {columns.find(c => c.key === colKey)?.label}</option>
              {uniqueColumnValues[colKey].map((val) => (
                <option key={val} value={val}>
                  {val}
                </option>
              ))}
            </select>
          ))}
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-line">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-700 cursor-pointer hover:bg-gray-100"
                  onClick={() => column.sortable && handleSort(column.key)}
                >
                  <div className="flex items-center gap-1">
                    {column.label}
                    {column.sortable && sortColumn === column.key && (
                      sortDirection === "asc" ? (
                        <ChevronUp className="h-3 w-3" />
                      ) : (
                        <ChevronDown className="h-3 w-3" />
                      )
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line bg-white">
            {filteredAndSortedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-sm text-muted"
                >
                  No records found
                </td>
              </tr>
            ) : (
              filteredAndSortedData.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={`hover:bg-gray-50 cursor-pointer transition-colors ${
                    onRowClick ? "hover:bg-teal-50" : ""
                  }`}
                  onClick={() => onRowClick && onRowClick(row)}
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className="px-4 py-3 text-sm text-gray-900"
                    >
                      {column.render ? column.render(row[column.key], row) : row[column.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-muted">
        Showing {filteredAndSortedData.length} of {data.length} records
      </div>
    </div>
  );
}
