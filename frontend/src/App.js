import React, {useState} from 'react';
import EventTable from './components/EventTable';
import {useEventApi} from "./hooks/useEventApi";
import Modal from "react-modal";
import moment from "moment";

const App = () => {

  const { updateEvent, createEvent, deleteEvent} = useEventApi();
  const [eventToEdit, setEventToEdit] = useState(null);
  const handleEditEvent = (event) => {console.log(event); console.log(moment.utc(event.at).format("YYYY-MM-DDTHH:mm")); setEventToEdit(event);};


  const genNewEvent = () => {setEventToEdit({at: '', data: ''})}
  const delEvent = () => {deleteEvent(eventToEdit.id).finally(setEventToEdit(null));};
  const createUpdateEvent = (e) => {
    e.preventDefault();
    const form = e.target;
    const updatedData = {
      data: form.elements.text.value,
      at: moment(form.elements.date.value).utc().toISOString()
    };
    (eventToEdit.id ? updateEvent(eventToEdit.id, updatedData) : createEvent(updatedData)).then((data) =>{
      console.log("data", data)
      //      setEvents(prev => [...prev, ...data.events]);
    }).finally(setEventToEdit(null))
    // TODO habdle callback, updating, inserting, deleting obj from current events subsets
  };

  const closeModal = () => {setEventToEdit(null);};

  return (

    <div className="page-container">
      <header>Header</header>
      <main className="main-content">
        <div className="table-container">
            <button onClick={genNewEvent}>New event</button>
            <EventTable onEdit={handleEditEvent}/>
        </div>
      </main>

      <footer>Footer</footer>
      <Modal isOpen={eventToEdit} onRequestClose={closeModal} contentLabel="Modal">
        <h2>{eventToEdit && eventToEdit.id ? "Update Event": "Create Event"}</h2>
        <form onSubmit={createUpdateEvent}>
          <div>
            <label>
              data:
              <input
                type="text"
                name="text"
                defaultValue={eventToEdit ? eventToEdit.data : ''}
                required
              />
            </label>
          </div>
          <div>
            <label>
              at:
              <input
                type="datetime-local"
                name="date"
                defaultValue={eventToEdit ? moment(eventToEdit.at).format("YYYY-MM-DDTHH:mm"): ''}
                required
              />
            </label>
          </div>
          <div>
            <button type="submit">{eventToEdit && eventToEdit.id ? "Update" : "Save"}</button>
            {eventToEdit && (
              <button onClick={delEvent}>Delete</button>
            )}
            <button type="button" onClick={closeModal}>Cancel</button>
          </div>
        </form>
      </Modal>

    </div>

  );
};

export default App;
