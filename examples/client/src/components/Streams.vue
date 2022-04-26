<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-10">
        <h1>Streams</h1>
        <hr><br><br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" v-b-modal.stream-add-modal>
            Add Stream
        </button>
        <br><br>
        <table class="table table-hover">
          <colgroup>
               <col span="1" style="width: 20%;">
               <col span="1" style="width: 70%;">
               <col span="1" style="width: 10%;">
          </colgroup>
          <thead>
            <tr>
              <th scope="col">Label</th>
              <th scope="col">Title</th>
              <th scope="col">Active?</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stream in streams" :key="stream.stream_id">
              <td>
                  <button type="button"
                          class="btn btn-link btn-sm"
                          v-b-modal.stream-update-modal
                          @click="editStream(stream)">
                      {{ stream.label }}
                  </button>
              </td>
              <td>
                  <button type="button"
                          class="btn btn-link btn-sm"
                          v-b-modal.stream-update-modal
                          @click="editStream(stream)">
                      {{ stream.title }}
                  </button>
              </td>
              <td>
                <span v-if="stream.active">Yes</span>
                <span v-else>No</span>
              </td>
              <td>
                <div class="btn-group" role="group">
                  <button type="button"
                          class="btn btn-primary btn-sm"
                          v-b-modal.stream-pubsub-modal
                          @click="setupPublishStream(stream)">Publish</button>
                  <button type="button"
                          class="btn btn-primary btn-sm"
                          v-b-modal.stream-pubsub-modal
                          @click="setupSubscribeStream(stream)">Subscribe</button>
                  <button type="button"
                          class="btn btn-danger btn-sm"
                          v-b-modal.stream-delete-modal
                          @click="setupDeleteStream(stream)">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
      <b-modal ref="addStreamModal"
             id="stream-add-modal"
             title="Add a new stream"
             hide-footer>
          <b-form @submit="onSubmit" @reset="onReset" class="w-100">
              <b-form-group id="form-label-group"
                          label="Label:"
                          label-for="form-label-input">
                <b-form-input id="form-label-input"
                              type="text"
                              v-model="addStreamForm.label"
                              required
                              placeholder="Enter label">
                </b-form-input>
              </b-form-group>
              <b-form-group id="form-title-group"
                        label="Title:"
                        label-for="form-title-input">
                <b-form-input id="form-title-input"
                            type="text"
                            v-model="addStreamForm.title"
                            required
                            placeholder="Enter title">
                </b-form-input>
              </b-form-group>
              <b-form-group id="form-description-group"
                        label="Description:"
                        label-for="form-description-input">
                <b-form-input id="form-description-input"
                            type="text"
                            v-model="addStreamForm.description"
                            required
                            placeholder="Enter description">
                </b-form-input>
              </b-form-group>

            <b-button type="submit" variant="primary">Add Stream</b-button>
            <b-button type="reset" variant="danger">Cancel</b-button>
          </b-form>
    </b-modal>
    <b-modal ref="editStreamModal"
             id="stream-update-modal"
             title="Update Stream"
             hide-footer>
      <b-form @submit="onSubmitUpdate" @reset="onResetUpdate" class="w-100">
          <b-form-group id="form-label-edit-group"
                        label="Label:"
                        label-for="form-label-edit-input">
              <b-form-input id="form-label-edit-input"
                            type="text"
                            v-model="editStreamForm.label"
                            required
                            placeholder="Enter label">
              </b-form-input>
            </b-form-group>
          <b-form-group id="form-title-edit-group"
                        label="Title:"
                        label-for="form-title-edit-input">
              <b-form-input id="form-title-edit-input"
                            type="text"
                            v-model="editStreamForm.title"
                            required
                            placeholder="Enter title">
              </b-form-input>
            </b-form-group>
          <b-form-group id="form-description-edit-group"
                        label="Description:"
                        label-for="form-description-edit-input">
            <b-form-input id="form-description-edit-input"
                          type="text"
                          v-model="editStreamForm.description"
                          required
                          placeholder="Enter description">
            </b-form-input>
            </b-form-group>
        <b-button-group>
          <b-button type="submit" variant="primary">Update Stream</b-button>
          <b-button type="reset" variant="danger">Cancel</b-button>
        </b-button-group>
      </b-form>
    </b-modal>
    <b-modal ref="deleteStreamModal"
             id="stream-delete-modal"
             title="Delete Stream"
             hide-footer>
        <table>
            <colgroup>
               <col span="1" style="width: 15%;">
               <col span="1" style="width: 85%;">
            </colgroup>
            <tbody>
                <tr><td><b>Label: </b></td><td>{{deleteStreamForm.label}}</td></tr>
                <tr><td><b>Title: </b></td><td>{{deleteStreamForm.title}}</td></tr>
            </tbody>
        </table>
        <br><br>
        <p align="right">
            <button type="button"
                    class="btn btn-warning btn-sm"
                    @click="onResetDelete()">
                    Cancel
            </button>
            <button type="button"
                    class="btn btn-danger btn-sm"
                    @click="onSubmitDelete()">
                    Delete
            </button>
        </p>
    </b-modal>
    <b-modal ref="pubsubStreamModal"
             id="stream-pubsub-modal"
             title="Publish / Subscribe Stream"
             hide-footer>
        <h3>{{pubsubForm.title}}</h3>
        <p>{{pubsubForm.description}}</p>
        <table>
            <colgroup>
               <col span="1" style="width: 25%;">
               <col span="1" style="width: 75%;">
            </colgroup>
            <tbody>
                <tr><td><b>{{pubsubForm.action}} URL: </b></td><td>{{pubsubForm.url}}</td></tr>
            </tbody>
        </table>
        <br><br>
        <p align="center">
            <button type="button"
                    class="btn btn-success btn-sm"
                    @click="onPubSubOK()">
                    OK
            </button>
        </p>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios';
import Alert from './Alert.vue';

export default {
  data() {
    return {
      streams: [],
      addStreamForm: {
        label: '',
        title: '',
        description: '',
      },
      editStreamForm: {
        stream_id: '',
        label: '',
        title: '',
        description: '',
      },
      deleteStreamForm: {
        stream_id: '',
        label: '',
        title: '',
      },
      pubsubForm: {
        action: '',
        label: '',
        title: '',
        description: '',
        url: '',
      },
      message: '',
      showMessage: false,
    };
  },

  components: {
    alert: Alert,
  },

  methods: {

    getStreams() {
      const path = 'http://localhost:5678/streams';
      axios.get(path)
        .then((res) => {
          this.streams = res.data.streams;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },

    addStream(payload) {
      const path = 'http://localhost:5678/stream';
      axios.post(path, payload)
        .then(() => {
          this.getStreams();
          this.message = 'Stream added!';
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.log(error);
          this.getStreams();
        });
    },

    initForm() {
      this.addStreamForm.label = '';
      this.addStreamForm.title = '';
      this.addStreamForm.description = '';
      this.editStreamForm.stream_id = '';
      this.editStreamForm.label = '';
      this.editStreamForm.title = '';
      this.editStreamForm.description = '';
      this.deleteStreamForm.stream_id = '';
      this.deleteStreamForm.label = '';
      this.deleteStreamForm.title = '';
      this.pubsubForm.action = '';
      this.pubsubForm.label = '';
      this.pubsubForm.title = '';
      this.pubsubForm.description = '';
      this.pubsubForm.url = '';
    },

    onSubmit(evt) {
      evt.preventDefault();
      this.$refs.addStreamModal.hide();
      const payload = {
        label: this.addStreamForm.label,
        title: this.addStreamForm.title,
        description: this.addStreamForm.description,
      };
      this.addStream(payload);
      this.initForm();
    },

    onReset(evt) {
      evt.preventDefault();
      this.$refs.addStreamModal.hide();
      this.initForm();
      this.getStreams();
    },

    editStream(stream) {
      this.editStreamForm.stream_id = stream.stream_id;
      this.editStreamForm.label = stream.label;
      this.editStreamForm.title = stream.title;
      this.editStreamForm.description = stream.description;
    },

    onSubmitUpdate(evt) {
      evt.preventDefault();
      this.$refs.editStreamModal.hide();
      const payload = {
        stream_id: this.editStreamForm.stream_id,
        label: this.editStreamForm.label,
        title: this.editStreamForm.title,
        description: this.editStreamForm.description,
      };
      this.updateStream(payload, this.editStreamForm.stream_id);
    },

    onResetUpdate(evt) {
      evt.preventDefault();
      this.$refs.editStreamModal.hide();
      this.initForm();
      this.getStreams();
    },

    updateStream(payload, streamId) {
      const path = `http://localhost:5678/stream/${streamId}`;
      axios.put(path, payload)
        .then(() => {
          this.getStreams();
          this.message = 'Stream updated!';
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getStreams();
        });
    },

    setupDeleteStream(stream) {
      this.deleteStreamForm.stream_id = stream.stream_id;
      this.deleteStreamForm.label = stream.label;
      this.deleteStreamForm.title = stream.title;
    },

    onSubmitDelete() {
      this.$refs.deleteStreamModal.hide();
      const payload = {
        stream_id: this.deleteStreamForm.stream_id,
      };
      this.initForm();
      this.deleteStream(payload);
    },

    onResetDelete() {
      this.$refs.deleteStreamModal.hide();
      this.initForm();
      this.getStreams();
    },

    deleteStream(payload) {
      const path = 'http://localhost:5678/stream';
      axios.delete(path, { data: payload })
        .then(() => {
          this.getStreams();
          this.message = 'Stream deleted!';
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getStreams();
        });
    },

    setupPublishStream(stream) {
      this.pubsubForm.action = 'Publish';
      this.pubsubForm.label = stream.label;
      this.pubsubForm.title = stream.title;
      this.pubsubForm.description = stream.description;
      this.pubsubForm.url = stream.publish_url;
    },

    setupSubscribeStream(stream) {
      this.pubsubForm.action = 'Subscribe';
      this.pubsubForm.label = stream.label;
      this.pubsubForm.title = stream.title;
      this.pubsubForm.description = stream.description;
      this.pubsubForm.url = stream.subscribe_url;
    },

    onPubSubOK() {
      this.$refs.pubsubStreamModal.hide();
      this.initForm();
    },
  },

  created() {
    this.getStreams();
  },
};
</script>
