const form = document.querySelector("#contact-form");
const idInput = document.querySelector("#contact-id");
const nameInput = document.querySelector("#name");
const phoneInput = document.querySelector("#phone");
const formMessage = document.querySelector("#form-message");
const formTitle = document.querySelector("#form-title");
const submitLabel = document.querySelector("#submit-label");
const cancelButton = document.querySelector("#cancel-button");
const contactList = document.querySelector("#contact-list");
const contactTemplate = document.querySelector("#contact-template");
const emptyState = document.querySelector("#empty-state");
const loading = document.querySelector("#loading");
const searchInput = document.querySelector("#search");
const countLabel = document.querySelector("#contact-count");

let contacts = [];

function showMessage(message, type = "error") {
  formMessage.textContent = message;
  formMessage.classList.toggle("success", type === "success");
}

function resetForm({ keepMessage = false } = {}) {
  form.reset();
  idInput.value = "";
  formTitle.textContent = "Novo contato";
  submitLabel.textContent = "Cadastrar contato";
  cancelButton.classList.add("hidden");
  if (!keepMessage) showMessage("");
}

function renderContacts() {
  const query = searchInput.value.trim().toLocaleLowerCase("pt-BR");
  const filteredContacts = contacts.filter((contact) =>
    `${contact.name} ${contact.phone}`.toLocaleLowerCase("pt-BR").includes(query)
  );

  contactList.replaceChildren();
  countLabel.textContent = contacts.length;
  emptyState.classList.toggle("hidden", filteredContacts.length !== 0);

  filteredContacts.forEach((contact) => {
    const item = contactTemplate.content.firstElementChild.cloneNode(true);
    const avatar = item.querySelector(".avatar");
    const name = item.querySelector(".contact-name");
    const phone = item.querySelector(".contact-phone");

    avatar.textContent = contact.name.charAt(0).toLocaleUpperCase("pt-BR");
    name.textContent = contact.name;
    phone.textContent = contact.phone;
    phone.href = `tel:${contact.phone.replace(/[^\d+]/g, "")}`;

    item.querySelector(".edit-button").addEventListener("click", () => editContact(contact));
    item.querySelector(".delete-button").addEventListener("click", () => deleteContact(contact));
    contactList.append(item);
  });
}

async function loadContacts() {
  loading.classList.remove("hidden");
  emptyState.classList.add("hidden");
  try {
    const response = await fetch("/api/contacts");
    if (!response.ok) throw new Error("Não foi possível carregar os contatos.");
    contacts = await response.json();
    renderContacts();
  } catch (error) {
    loading.textContent = error.message;
  } finally {
    loading.classList.add("hidden");
  }
}

function editContact(contact) {
  idInput.value = contact.id;
  nameInput.value = contact.name;
  phoneInput.value = contact.phone;
  formTitle.textContent = "Editar contato";
  submitLabel.textContent = "Salvar alterações";
  cancelButton.classList.remove("hidden");
  showMessage("");
  nameInput.focus();
}

async function deleteContact(contact) {
  const confirmed = window.confirm(`Excluir o contato de ${contact.name}?`);
  if (!confirmed) return;

  const response = await fetch(`/api/contacts/${contact.id}`, { method: "DELETE" });
  if (!response.ok) {
    showMessage("Não foi possível excluir o contato.");
    return;
  }

  if (idInput.value === String(contact.id)) resetForm();
  await loadContacts();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const contactId = idInput.value;
  const response = await fetch(contactId ? `/api/contacts/${contactId}` : "/api/contacts", {
    method: contactId ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: nameInput.value,
      phone: phoneInput.value,
    }),
  });
  const result = await response.json();

  if (!response.ok) {
    showMessage(result.error || "Não foi possível salvar o contato.");
    return;
  }

  resetForm({ keepMessage: true });
  showMessage(contactId ? "Contato atualizado com sucesso." : "Contato cadastrado com sucesso.", "success");
  await loadContacts();
  nameInput.focus();
});

cancelButton.addEventListener("click", () => resetForm());
searchInput.addEventListener("input", renderContacts);
loadContacts();
