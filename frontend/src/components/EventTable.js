import React, { useState, useEffect, useRef, useCallback } from "react";
import { useReactTable, getCoreRowModel, flexRender } from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import {useEventApi} from "../hooks/useEventApi";
import DatePickerTooltip from "./DatePickerTooltip";
import moment from 'moment';
import "react-day-picker/style.css";


const PAGE_SIZE = 200;

function formatDate(date) {
  return new Date(date).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "medium"
  });
}
export default function EventTable({onEdit}) {

  const { fetchEvents } = useEventApi();
  const parentRef = useRef();
  const [selectedRange, setSelectedRange] = useState({ from: null, to: null });
  const [order, setOrder] = useState("desc");
  const [open, setOpen] = useState(false);
  const [cursor, setCursor] = useState(null);
  const [events, setEvents] = useState([]);
  const [hasNextPage, setHasNextPage] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const handleDateChange = (datesRange) => {setSelectedRange(datesRange || { from: null, to: null });};
  const handleClick = (event) => {setOpen(true);};
  const handleClose = () => {setOpen(false);};
  const handleSort = () => {setOrder(prev => prev === "asc" ? "desc" : "asc");};


  function setStartOfDayLocalToUTCIso(date) {
    return date ? moment(date).startOf('day').utc().toISOString() : null;
  }

  function setEndOfDayLocalToUTCIso(date) {
    return date ? moment(date).endOf('day').utc().toISOString() : null;
  }

  const fetchData = useCallback(async (selectedRange, order, cursor) => {
    setIsLoading(true);
    fetchEvents(cursor, setStartOfDayLocalToUTCIso(selectedRange.from), setEndOfDayLocalToUTCIso( selectedRange.to), order, PAGE_SIZE).then((data) =>{
      setEvents(prev => [...prev, ...data.events]);
      setCursor(data.next_cursor);
      setHasNextPage(data.next_cursor);
      setIsLoading(false);
    })
  }, []);

  useEffect(() => {
    setEvents([]);
    setCursor(null);
    setHasNextPage(true);
    fetchData(selectedRange, order, null);
  }, [selectedRange, order]);  // TODO race condition in fetch data

  const loadMoreData = () => {if (!isLoading && hasNextPage) {fetchData(cursor, order, cursor);}};
  const columns = [
    {
      header: "Data",
      accessorKey: "data",
    },
    {
      accessorKey: "at",
      cell: (info) => formatDate(info.getValue()),
      header: (props) => (
        <>

          <button onClick={handleSort}>
            {order}
          </button>
          At
          <DatePickerTooltip
            selectedRange={selectedRange}
            onDateChange={handleDateChange}
            open={open}
            handleClick={handleClick}
            handleClose={handleClose}
          />
        </>
      ),
    },

  ];

  const table = useReactTable({
    data: events || [],
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const rowVirtualizer = useVirtualizer({
    count: table.getRowModel().rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 25,
    overscan: 50,
  });




  const rows = table.getRowModel().rows;

return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", borderBottom: "1px solid #ccc" }}>
        {table.getHeaderGroups().map((headerGroup) =>
          headerGroup.headers.map((header) => (
            <div
              key={header.id}
              style={{ flex: 1, fontWeight: "bold"}}
            >
              {flexRender(header.column.columnDef.header, header.getContext())}
            </div>
          ))
        )}
      </div>

      {/* Virtualized Rows */}
      <div
        ref={parentRef}
        style={{
          height: `300px`,
          overflow: "auto",
        }}
        onScroll={() => {
          const bottom =
            parentRef.current.scrollHeight === parentRef.current.scrollTop + parentRef.current.clientHeight;
          if (bottom) {
            loadMoreData();
          }
        }}
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            position: "relative",
          }}
        >
          {rowVirtualizer.getVirtualItems().map((virtualRow) => {
            const row = rows[virtualRow.index];
            return (
              <div
                className="table-row"
                key={row.id}
                onClick={() => onEdit(row.original)}
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  transform: `translateY(${virtualRow.start}px)`,
                  display: "flex",
                  backgroundColor: virtualRow.index % 2 === 0 ? "#f9f9f9" : "#ffffff",
                  width: "100%",
                  cursor: "pointer",
                  transition: "background-color 0.2s",
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <div key={cell.id} style={{ flex: 1 }}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>

      {isLoading && <div>Cargando...</div>}
      {!hasNextPage && <div>No hay más datos</div>}
    </div>
  );

}