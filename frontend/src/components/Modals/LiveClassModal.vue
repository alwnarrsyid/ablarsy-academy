<template>
	<Dialog
		v-model="show"
		:options="{
			title: __('Create a Live Class'),
			size: 'xl',
			actions: [
				{
					label: 'Submit',
					variant: 'solid',
					onClick: ({ close }) => submitLiveClass(close),
				},
			],
		}"
	>
		<template #body-content>
			<div class="flex flex-col gap-4">
				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-4">
						<FormControl
							type="text"
							v-model="liveClass.title"
							:label="__('Title')"
							:required="true"
						/>
						<FormControl
							v-model="liveClass.date"
							type="date"
							:label="__('Date')"
							:required="true"
						/>
						<Tooltip :text="__('Duration of the live class in minutes')">
							<FormControl
								type="number"
								v-model="liveClass.duration"
								:label="__('Duration')"
								:required="true"
							/>
						</Tooltip>
						<div class="space-y-1.5">
							<label class="block text-ink-gray-5 text-xs">
								{{ __('Meeting Platform') }}
								<span class="text-ink-red-3">*</span>
							</label>
							<FormControl
								v-model="liveClass.meeting_platform"
								type="select"
								:options="getPlatformOptions()"
							/>
						</div>
					</div>
					<div class="space-y-4">
						<Tooltip
							:text="
								__(
									'Time must be in 24 hour format (HH:mm). Example 11:30 or 22:00'
								)
							"
						>
							<FormControl
								v-model="liveClass.time"
								type="time"
								:label="__('Time')"
								:required="true"
							/>
						</Tooltip>

						<div class="space-y-1.5">
							<label class="block text-ink-gray-5 text-xs" for="batchTimezone">
								{{ __('Timezone') }}
								<span class="text-ink-red-3">*</span>
							</label>
							<Autocomplete
								@update:modelValue="(opt) => (liveClass.timezone = opt.value)"
								:modelValue="liveClass.timezone"
								:options="getTimezoneOptions()"
								:required="true"
							/>
						</div>
						<FormControl
							v-model="liveClass.auto_recording"
							type="select"
							:options="getRecordingOptions()"
							:label="__('Auto Recording')"
							v-if="liveClass.meeting_platform === 'Zoom'"
						/>
						<!-- Google Meet Link Field -->
						<div v-if="liveClass.meeting_platform === 'Google Meet'" class="space-y-1.5">
							<label class="block text-ink-gray-5 text-xs">
								{{ __('Google Meet Link') }}
								<span class="text-ink-red-3">*</span>
							</label>
							<FormControl
								v-model="liveClass.google_meet_link"
								type="text"
								placeholder="https://meet.google.com/xxx-xxxx-xxx"
							/>
							<p class="text-xs text-ink-gray-4">
								{{ __('Create a meeting at') }}
								<a href="https://meet.google.com/new" target="_blank" class="text-blue-600 hover:underline">meet.google.com/new</a>
								{{ __('and paste the link here') }}
							</p>
						</div>
					</div>
				</div>
				<FormControl
					v-model="liveClass.description"
					type="textarea"
					:label="__('Description')"
				/>
			</div>
		</template>
	</Dialog>
</template>
<script setup>
import {
	Dialog,
	createResource,
	Tooltip,
	FormControl,
	Autocomplete,
	toast,
} from 'frappe-ui'
import { reactive, inject, onMounted, computed, watch } from 'vue'
import { getTimezones, getUserTimezone } from '@/utils/'

const show = defineModel()
const emit = defineEmits(['reload'])
const user = inject('$user')
const dayjs = inject('$dayjs')

const props = defineProps({
	batch: {
		type: String,
		required: true,
	},
	zoomAccount: {
		type: String,
		default: '',
	},
	googleMeetAccount: {
		type: String,
		default: '',
	},
})

// Determine default platform based on available accounts
const getDefaultPlatform = () => {
	if (props.zoomAccount) return 'Zoom'
	if (props.googleMeetAccount) return 'Google Meet'
	return 'Zoom'
}

let liveClass = reactive({
	title: '',
	description: '',
	date: '',
	time: '',
	duration: '',
	timezone: '',
	auto_recording: 'No Recording',
	batch: props.batch,
	host: user.data?.name || '',
	meeting_platform: 'Zoom',
	google_meet_link: '',
})

onMounted(() => {
	liveClass.timezone = getUserTimezone()
	liveClass.meeting_platform = getDefaultPlatform()
})

// Watch for changes in available accounts
watch(() => [props.zoomAccount, props.googleMeetAccount], () => {
	liveClass.meeting_platform = getDefaultPlatform()
})

const getPlatformOptions = () => {
	return [
		{ label: 'Zoom', value: 'Zoom' },
		{ label: 'Google Meet', value: 'Google Meet' }
	]
}

const getTimezoneOptions = () => {
	return getTimezones().map((timezone) => {
		return {
			label: timezone,
			value: timezone,
		}
	})
}

const getRecordingOptions = () => {
	return [
		{
			label: 'No Recording',
			value: 'No Recording',
		},
		{
			label: 'Local',
			value: 'Local',
		},
		{
			label: 'Cloud',
			value: 'Cloud',
		},
	]
}

const createZoomLiveClass = createResource({
	url: 'lms.lms.doctype.lms_batch.lms_batch.create_live_class',
	makeParams(values) {
		return {
			doctype: 'LMS Live Class',
			batch_name: values.batch,
			zoom_account: props.zoomAccount,
			...values,
		}
	},
})

const createGoogleMeetLiveClass = createResource({
	url: 'frappe.client.insert',
	makeParams(values) {
		return {
			doc: {
				doctype: 'LMS Live Class',
				batch_name: values.batch,
				title: values.title,
				duration: values.duration,
				date: values.date,
				time: values.time,
				timezone: values.timezone,
				host: values.host,
				description: values.description,
				meeting_platform: 'Google Meet',
				google_meet_link: values.google_meet_link,
				join_url: values.google_meet_link,
				start_url: values.google_meet_link,
			}
		}
	},
})

const submitLiveClass = (close) => {
	const resource = liveClass.meeting_platform === 'Google Meet'
		? createGoogleMeetLiveClass
		: createZoomLiveClass

	return resource.submit(liveClass, {
		validate() {
			validateFormFields()
		},
		onSuccess() {
			emit('reload')
			refreshForm()
			close()
		},
		onError(err) {
			toast.error(err.messages?.[0] || err)
		},
	})
}

const validateFormFields = () => {
	if (!liveClass.title) {
		return __('Please enter a title.')
	}
	if (!liveClass.date) {
		return __('Please select a date.')
	}
	if (!liveClass.time) {
		return __('Please select a time.')
	}
	if (!liveClass.timezone) {
		return __('Please select a timezone.')
	}
	if (!valideTime()) {
		return __('Please enter a valid time in the format HH:mm.')
	}
	const liveClassDateTime = dayjs(`${liveClass.date}T${liveClass.time}`).tz(
		liveClass.timezone,
		true
	)
	if (
		liveClassDateTime.isSameOrBefore(
			dayjs().tz(liveClass.timezone, false),
			'minute'
		)
	) {
		return __('Please select a future date and time.')
	}
	if (!liveClass.duration) {
		return __('Please select a duration.')
	}
	// Validate platform-specific requirements
	if (liveClass.meeting_platform === 'Zoom' && !props.zoomAccount) {
		return __('Please add a Zoom account to the batch first.')
	}
	if (liveClass.meeting_platform === 'Google Meet' && !liveClass.google_meet_link) {
		return __('Please enter a Google Meet link.')
	}
	// Validate Google Meet link format
	if (liveClass.meeting_platform === 'Google Meet' && liveClass.google_meet_link) {
		if (!liveClass.google_meet_link.includes('meet.google.com')) {
			return __('Please enter a valid Google Meet link.')
		}
	}
}

const valideTime = () => {
	let time = liveClass.time.split(':')
	if (time.length != 2) {
		return false
	}
	if (time[0] < 0 || time[0] > 23) {
		return false
	}
	if (time[1] < 0 || time[1] > 59) {
		return false
	}
	return true
}

const refreshForm = () => {
	liveClass.title = ''
	liveClass.description = ''
	liveClass.date = ''
	liveClass.time = ''
	liveClass.duration = ''
	liveClass.timezone = getUserTimezone()
	liveClass.auto_recording = 'No Recording'
	liveClass.meeting_platform = 'Zoom'
	liveClass.google_meet_link = ''
}
</script>

