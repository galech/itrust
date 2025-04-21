import React, { useState, useRef } from "react";
import { Popover } from "@mui/material";
import { DayPicker } from "react-day-picker"; // Asegúrate de tener esta librería instalada

export default function DatePickerTooltip({ onDateChange, selectedRange, handleClose, handleClick, open}) {

  const buttonRef = useRef(null);

  return (
    <span>
      <button ref={buttonRef} onClick={handleClick}>Between {selectedRange.from ? selectedRange.from.toLocaleDateString() : "##/##/##"} - {selectedRange.to ? selectedRange.to.toLocaleDateString() : "##/##/##"}</button>
      <Popover
        open={open}
        anchorEl={buttonRef.current}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        transformOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <DayPicker
          mode="range"
          selected={selectedRange}
          onSelect={onDateChange}
          dateFormat="P"
          placeholderText="Select a date"
        />
      </Popover>
    </span>
  );
}