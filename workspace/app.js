// app.js - Book My Show logic

// Hard-coded show data
const shows = [
  { id: 1, title: "The Lion King", genre: "Musical", price: 49.99, image: "https://picsum.photos/seed/lionking/400/200" },
  { id: 2, title: "Hamilton", genre: "Musical", price: 59.99, image: "https://picsum.photos/seed/hamilton/400/200" },
  { id: 3, title: "Wicked", genre: "Musical", price: 54.99, image: "https://picsum.photos/seed/wicked/400/200" },
  { id: 4, title: "The Phantom of the Opera", genre: "Musical", price: 59.99, image: "https://picsum.photos/seed/phantom/400/200" }
];

function renderShows() {
  const container = document.getElementById('shows');
  container.innerHTML = '';
  shows.forEach(show => {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow p-4 flex flex-col';
    card.innerHTML = `
      <img src="${show.image}" alt="${show.title}" class="h-48 w-full object-cover rounded" />
      <h3 class="mt-4 text-xl font-semibold">${show.title}</h3>
      <p class="text-gray-600">${show.genre}</p>
      <p class="mt-2 font-medium">$${show.price.toFixed(2)}</p>
      <button class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700" onclick="openBookingForm(${show.id})">Book Now</button>
    `;
    container.appendChild(card);
  });
}

function openBookingForm(showId) {
  const show = shows.find(s => s.id === showId);
  const modal = document.getElementById('modal');
  const content = document.getElementById('modal-content');
  content.innerHTML = `
    <p><strong>Show:</strong> ${show.title}</p>
    <p><strong>Price:</strong> $${show.price.toFixed(2)}</p>
    <form id="booking-form" class="mt-4">
      <label class="block mb-2">Date</label>
      <input type="text" id="booking-date" class="w-full p-2 border rounded" required />
      <label class="block mt-2 mb-2">Tickets</label>
      <input type="number" id="booking-qty" min="1" value="1" class="w-full p-2 border rounded" required />
      <label class="block mt-2 mb-2">Name</label>
      <input type="text" id="booking-name" class="w-full p-2 border rounded" required />
      <label class="block mt-2 mb-2">Email</label>
      <input type="email" id="booking-email" class="w-full p-2 border rounded" required />
      <button type="submit" class="mt-4 w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Confirm Booking</button>
    </form>
  `;
  modal.classList.remove('hidden');
  flatpickr('#booking-date', { minDate: 'today' });

  document.getElementById('booking-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const booking = {
      showId: show.id,
      date: document.getElementById('booking-date').value,
      qty: document.getElementById('booking-qty').value,
      name: document.getElementById('booking-name').value,
      email: document.getElementById('booking-email').value
    };
    localStorage.setItem('lastBooking', JSON.stringify(booking));
    content.innerHTML = `<p>Thank you, ${booking.name}! Your booking for <strong>${show.title}</strong> on <strong>${booking.date}</strong> has been confirmed.</p>`;
  });
}

function closeModal() {
  console.log('closeModal called');
  const modal = document.getElementById('modal');
  modal.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
  renderShows();
  document.getElementById('close-modal').addEventListener('click', closeModal);
});
