import axios from 'axios';
const EVENTS_API_URL = "http://localhost:8000/events/";
export const useEventApi = () => {

  const fetchEvents = async (cursor = null, start, end, order, pageSize = 50) => {
    const response = await axios.get(EVENTS_API_URL, {
      params: { cursor, pageSize, start, end, order}
    });
    return response.data; // contiene { events, next_cursor }
  };

  const createEvent = async (eventData) => {
    const response = await axios.post(EVENTS_API_URL, eventData);
    return response.data;
  };

  const deleteEvent = async (eventId) => {
    const response = await axios.delete(`${EVENTS_API_URL}${eventId}`);
    return response.data;
  };

  const updateEvent = async (eventId, updatedData) => {
    const response = await axios.put(`${EVENTS_API_URL}${eventId}`, updatedData);
    return response.data;
  };

  return { fetchEvents, createEvent, deleteEvent, updateEvent };
};