<template>
	<div class="flex h-full flex-col md:flex-row bg-white">
		<!-- Internal Sidebar (Desktop Only) -->
		<div class="w-64 border-r bg-gray-50 h-full overflow-y-auto hidden md:block flex-shrink-0">
			<div class="p-5">
				<h2 class="font-bold text-base text-gray-800 mb-5">Developer API</h2>
				<div class="space-y-1">
					<button
						v-for="section in sections"
						:key="section.id"
						@click="activeSection = section.id"
						class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
						:class="activeSection === section.id
							? 'bg-blue-600 text-white'
							: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'"
					>
						{{ section.title }}
					</button>
				</div>
			</div>
		</div>

		<!-- Main Content -->
		<div class="flex-1 h-full overflow-y-auto">
			<!-- Mobile Category Selector -->
			<div class="md:hidden p-4 border-b bg-gray-50 overflow-x-auto">
				<div class="flex gap-2">
					<button
						v-for="section in sections"
						:key="section.id"
						@click="activeSection = section.id"
						class="whitespace-nowrap px-4 py-2 rounded-full text-sm font-semibold border-2 transition-colors"
						:class="activeSection === section.id
							? 'bg-blue-600 text-white border-blue-600'
							: 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'"
					>
						{{ section.title }}
					</button>
				</div>
			</div>

			<div class="p-6 md:p-10">
				<!-- Page Header -->
				<div class="mb-10">
					<h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">{{ activeSectionInfo.title }}</h1>
					<p class="text-gray-500 text-base">{{ activeSectionInfo.description }}</p>
				</div>

				<!-- API Items -->
				<div class="space-y-12">
					<div
						v-for="api in activeSectionInfo.apis"
						:key="api.name"
						class="border border-gray-200 rounded-xl overflow-hidden shadow-sm bg-white"
					>
						<!-- API Header -->
						<div class="flex items-center gap-3 px-5 py-4 bg-gray-50 border-b border-gray-200">
							<span
								class="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wide"
								:class="getMethodClass(api.method)"
							>
								{{ api.method }}
							</span>
							<code class="text-sm text-gray-800 font-mono font-medium break-all">
								{{ api.endpoint }}
							</code>
						</div>

						<!-- API Body: 2 Column Grid -->
						<div class="grid grid-cols-1 lg:grid-cols-2">
							<!-- Left Column: Details -->
							<div class="p-5 lg:border-r border-gray-200">
								<div class="mb-5">
									<h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Description</h4>
									<p class="text-gray-700 text-sm leading-relaxed">{{ api.description }}</p>
								</div>

								<div v-if="api.params && api.params.length">
									<h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Parameters</h4>
									<div class="space-y-3">
										<div
											v-for="param in api.params"
											:key="param.name"
											class="bg-gray-50 rounded-lg p-3 border border-gray-100"
										>
											<div class="flex items-center gap-2 mb-1">
												<code class="text-sm font-mono font-semibold text-gray-900">{{ param.name }}</code>
												<span class="text-xs px-1.5 py-0.5 rounded bg-gray-200 text-gray-500 font-medium">{{ param.type }}</span>
												<span
													v-if="param.required"
													class="text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-600 font-semibold"
												>Required</span>
											</div>
											<p class="text-xs text-gray-500">{{ param.desc }}</p>
										</div>
									</div>
								</div>
							</div>

							<!-- Right Column: Code Example -->
							<div class="p-5 bg-gray-900 text-white">
								<div class="flex items-center justify-between mb-3">
									<div class="flex gap-2">
										<button
											v-for="lang in ['cURL', 'Python']"
											:key="lang"
											@click="api.activeLang = lang"
											class="px-3 py-1.5 rounded-md text-xs font-semibold transition-colors"
											:class="api.activeLang === lang ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
										>
											{{ lang }}
										</button>
									</div>
									<button @click="copyCode(api.examples[api.activeLang])" class="p-1.5 rounded hover:bg-gray-700 text-gray-400 hover:text-white">
										<Copy class="w-4 h-4" />
									</button>
								</div>
								<pre class="text-xs leading-relaxed font-mono whitespace-pre-wrap break-all overflow-x-auto text-gray-100">{{ api.examples[api.activeLang] }}</pre>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { toast } from 'frappe-ui'
import { Copy } from 'lucide-vue-next'

const activeSection = ref('courses')

const copyCode = (code) => {
	navigator.clipboard.writeText(code)
	toast.success('Copied to clipboard')
}

const getMethodClass = (method) => {
	const map = {
		'GET': 'bg-blue-100 text-blue-700',
		'POST': 'bg-green-100 text-green-700',
		'PUT': 'bg-yellow-100 text-yellow-700',
		'DELETE': 'bg-red-100 text-red-700'
	}
	return map[method] || 'bg-gray-100 text-gray-700'
}

const sections = [
	{ id: 'courses', title: 'Courses', description: 'APIs for managing LMS courses.' },
	{ id: 'batches', title: 'Batches', description: 'APIs for managing batch programs.' },
	{ id: 'enrollments', title: 'Enrollments', description: 'APIs for course and batch enrollments.' },
	{ id: 'payments', title: 'Payments', description: 'APIs for payment management (Admin only).' },
	{ id: 'certificates', title: 'Certificates', description: 'APIs for certificate management and verification.' },
	{ id: 'quizzes', title: 'Quizzes', description: 'APIs for quiz management.' },
	{ id: 'live_classes', title: 'Live Classes', description: 'APIs for live class scheduling.' },
	{ id: 'commissions', title: 'Commissions', description: 'APIs for referral commission management.' },
	{ id: 'categories', title: 'Categories', description: 'APIs for category management.' },
	{ id: 'statistics', title: 'Statistics', description: 'APIs for dashboard and revenue statistics.' },
	{ id: 'users', title: 'Users', description: 'APIs for user profile management.' }
]

const apis = reactive({
	courses: [
		{
			name: 'List Courses',
			endpoint: 'lms.lms.api.api_get_courses',
			method: 'GET',
			description: 'Get list of courses with optional filters. Supports pagination.',
			activeLang: 'cURL',
			params: [
				{ name: 'published', type: 'Integer', desc: '0 or 1 to filter by published status', required: false },
				{ name: 'paid_course', type: 'Integer', desc: '0 or 1 to filter by paid status', required: false },
				{ name: 'category', type: 'String', desc: 'Category name to filter', required: false },
				{ name: 'featured', type: 'Integer', desc: '0 or 1 to filter featured courses', required: false },
				{ name: 'upcoming', type: 'Integer', desc: '0 or 1 to filter upcoming courses', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset (default 0)', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results (default 20)', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_courses?published=1&paid_course=1&limit=10"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_courses"
params = {"published": 1, "paid_course": 1, "limit": 10}

response = requests.get(url, params=params)
print(response.json())`
			}
		},
		{
			name: 'Get Course Detail',
			endpoint: 'lms.lms.api.api_get_course',
			method: 'GET',
			description: 'Get single course with chapters and lessons.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Course ID/Name', required: true }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_course?name=python-basics"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_course"
params = {"name": "python-basics"}

response = requests.get(url, params=params)
print(response.json())`
			}
		},
		{
			name: 'Update Course',
			endpoint: 'lms.lms.api.api_update_course',
			method: 'POST',
			description: 'Update course details. Admin/Moderator/Course Creator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Course ID/Name - REQUIRED for identifying which course to update', required: true },
				{ name: 'title', type: 'String', desc: 'Course title', required: false },
				{ name: 'description', type: 'String', desc: 'Full course description (HTML)', required: false },
				{ name: 'short_introduction', type: 'String', desc: 'Short course description', required: false },
				{ name: 'published', type: 'Integer', desc: '0 or 1', required: false },
				{ name: 'paid_course', type: 'Integer', desc: '0 or 1', required: false },
				{ name: 'course_price', type: 'Float', desc: 'Course price', required: false },
				{ name: 'currency', type: 'String', desc: 'Currency code (IDR, USD, etc)', required: false },
				{ name: 'category', type: 'String', desc: 'Category name', required: false },
				{ name: 'featured', type: 'Integer', desc: '0 or 1', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_update_course" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "name=python-basics" \\
  -d "title=Python Basics Updated" \\
  -d "published=1" \\
  -d "course_price=150000"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_update_course"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {
    "name": "python-basics",
    "title": "Python Basics Updated",
    "published": 1,
    "course_price": 150000
}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	batches: [
		{
			name: 'List Batches',
			endpoint: 'lms.lms.api.api_get_batches',
			method: 'GET',
			description: 'Get list of batches with optional filters.',
			activeLang: 'cURL',
			params: [
				{ name: 'published', type: 'Integer', desc: '0 or 1 to filter by published status', required: false },
				{ name: 'paid_batch', type: 'Integer', desc: '0 or 1 to filter by paid status', required: false },
				{ name: 'category', type: 'String', desc: 'Category name to filter', required: false },
				{ name: 'medium', type: 'String', desc: 'Medium (Online/Offline)', required: false },
				{ name: 'start_date_from', type: 'String', desc: 'Filter batches starting from this date (YYYY-MM-DD)', required: false },
				{ name: 'start_date_to', type: 'String', desc: 'Filter batches starting until this date (YYYY-MM-DD)', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_batches?published=1&medium=Online&limit=10"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_batches"
params = {"published": 1, "medium": "Online", "limit": 10}

response = requests.get(url, params=params)
print(response.json())`
			}
		},
		{
			name: 'Get Batch Detail',
			endpoint: 'lms.lms.api.api_get_batch',
			method: 'GET',
			description: 'Get single batch with courses, instructors, and seat availability.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Batch ID/Name', required: true }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_batch?name=batch-2024-january"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_batch"
params = {"name": "batch-2024-january"}

response = requests.get(url, params=params)
print(response.json())`
			}
		},
		{
			name: 'Update Batch',
			endpoint: 'lms.lms.api.api_update_batch',
			method: 'POST',
			description: 'Update batch details. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Batch ID/Name - REQUIRED', required: true },
				{ name: 'title', type: 'String', desc: 'Batch title', required: false },
				{ name: 'description', type: 'String', desc: 'Short description', required: false },
				{ name: 'published', type: 'Integer', desc: '0 or 1', required: false },
				{ name: 'paid_batch', type: 'Integer', desc: '0 or 1', required: false },
				{ name: 'amount', type: 'Float', desc: 'Batch price', required: false },
				{ name: 'currency', type: 'String', desc: 'Currency code', required: false },
				{ name: 'start_date', type: 'String', desc: 'Start date (YYYY-MM-DD)', required: false },
				{ name: 'end_date', type: 'String', desc: 'End date (YYYY-MM-DD)', required: false },
				{ name: 'seat_count', type: 'Integer', desc: 'Maximum seats', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_update_batch" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "name=batch-2024-january" \\
  -d "seat_count=50" \\
  -d "published=1"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_update_batch"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {
    "name": "batch-2024-january",
    "seat_count": 50,
    "published": 1
}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	enrollments: [
		{
			name: 'List Course Enrollments',
			endpoint: 'lms.lms.api.api_get_enrollments',
			method: 'GET',
			description: 'Get list of course enrollments. Admin can see all, users see their own.',
			activeLang: 'cURL',
			params: [
				{ name: 'course', type: 'String', desc: 'Filter by course ID/name', required: false },
				{ name: 'member', type: 'String', desc: 'Filter by member email (Admin only)', required: false },
				{ name: 'progress_min', type: 'Integer', desc: 'Filter enrollments with progress >= this value', required: false },
				{ name: 'progress_max', type: 'Integer', desc: 'Filter enrollments with progress <= this value', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_enrollments?course=python-basics&progress_min=50" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_enrollments"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"course": "python-basics", "progress_min": 50}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Create Enrollment',
			endpoint: 'lms.lms.api.api_create_enrollment',
			method: 'POST',
			description: 'Create course enrollment. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'course', type: 'String', desc: 'Course ID/name', required: true },
				{ name: 'member', type: 'String', desc: 'User email', required: true },
				{ name: 'payment', type: 'String', desc: 'Payment ID (optional)', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_create_enrollment" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "course=python-basics" \\
  -d "member=student@example.com"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_create_enrollment"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"course": "python-basics", "member": "student@example.com"}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		},
		{
			name: 'Update Enrollment',
			endpoint: 'lms.lms.api.api_update_enrollment',
			method: 'POST',
			description: 'Update enrollment progress. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Enrollment ID - REQUIRED', required: true },
				{ name: 'progress', type: 'Integer', desc: 'Progress percentage (0-100)', required: false },
				{ name: 'current_lesson', type: 'String', desc: 'Current lesson ID/name', required: false },
				{ name: 'purchased_certificate', type: 'Integer', desc: '0 or 1', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_update_enrollment" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "name=ENRL-00001" \\
  -d "progress=100"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_update_enrollment"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"name": "ENRL-00001", "progress": 100}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		},
		{
			name: 'List Batch Enrollments',
			endpoint: 'lms.lms.api.api_get_batch_enrollments',
			method: 'GET',
			description: 'Get list of batch enrollments.',
			activeLang: 'cURL',
			params: [
				{ name: 'batch', type: 'String', desc: 'Filter by batch ID/name', required: false },
				{ name: 'member', type: 'String', desc: 'Filter by member email (Admin only)', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_batch_enrollments?batch=batch-2024" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_batch_enrollments"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"batch": "batch-2024"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Create Batch Enrollment',
			endpoint: 'lms.lms.api.api_create_batch_enrollment',
			method: 'POST',
			description: 'Create batch enrollment. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'batch', type: 'String', desc: 'Batch ID/name', required: true },
				{ name: 'member', type: 'String', desc: 'User email', required: true },
				{ name: 'payment', type: 'String', desc: 'Payment ID (optional)', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_create_batch_enrollment" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "batch=batch-2024" \\
  -d "member=student@example.com"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_create_batch_enrollment"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"batch": "batch-2024", "member": "student@example.com"}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	payments: [
		{
			name: 'List Payments',
			endpoint: 'lms.lms.api.api_get_payments',
			method: 'GET',
			description: 'Get list of payments. Admin only.',
			activeLang: 'cURL',
			params: [
				{ name: 'member', type: 'String', desc: 'Filter by member email', required: false },
				{ name: 'status', type: 'String', desc: 'Filter by status (Pending/Paid/Expired/Cancelled)', required: false },
				{ name: 'payment_for_document', type: 'String', desc: 'Filter by batch/course name', required: false },
				{ name: 'date_from', type: 'String', desc: 'Filter payments from this date (YYYY-MM-DD)', required: false },
				{ name: 'date_to', type: 'String', desc: 'Filter payments until this date (YYYY-MM-DD)', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_payments?status=Paid&date_from=2024-01-01" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_payments"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"status": "Paid", "date_from": "2024-01-01"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Get Payment Detail',
			endpoint: 'lms.lms.api.api_get_payment',
			method: 'GET',
			description: 'Get single payment detail. Admin only.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Payment ID', required: true }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_payment?name=PAY-00001" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_payment"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"name": "PAY-00001"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Update Payment',
			endpoint: 'lms.lms.api.api_update_payment',
			method: 'POST',
			description: 'Update payment status. Admin only. Useful for marking manual payments.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Payment ID - REQUIRED', required: true },
				{ name: 'status', type: 'String', desc: 'Payment status (Pending/Paid/Expired/Cancelled)', required: false },
				{ name: 'payment_received', type: 'Integer', desc: '0 or 1 to mark if payment has been received', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_update_payment" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "name=PAY-00001" \\
  -d "status=Paid" \\
  -d "payment_received=1"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_update_payment"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"name": "PAY-00001", "status": "Paid", "payment_received": 1}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	certificates: [
		{
			name: 'List Certificates',
			endpoint: 'lms.lms.api.api_get_certificates',
			method: 'GET',
			description: 'Get list of certificates. Admin can see all, users see their own.',
			activeLang: 'cURL',
			params: [
				{ name: 'member', type: 'String', desc: 'Filter by member email (Admin only)', required: false },
				{ name: 'course', type: 'String', desc: 'Filter by course ID/name', required: false },
				{ name: 'batch_name', type: 'String', desc: 'Filter by batch ID/name', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_certificates?course=python-basics" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_certificates"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"course": "python-basics"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Verify Certificate',
			endpoint: 'lms.lms.api.api_verify_certificate',
			method: 'GET',
			description: 'Public API to verify certificate authenticity. No authentication required.',
			activeLang: 'cURL',
			params: [
				{ name: 'certificate_id', type: 'String', desc: 'Certificate ID to verify', required: true }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_verify_certificate?certificate_id=CERT-00001"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_verify_certificate"
params = {"certificate_id": "CERT-00001"}

response = requests.get(url, params=params)
print(response.json())`
			}
		},
		{
			name: 'Issue Certificate',
			endpoint: 'lms.lms.api.api_issue_certificate',
			method: 'POST',
			description: 'Issue a new certificate. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'member', type: 'String', desc: 'User email', required: true },
				{ name: 'course', type: 'String', desc: 'Course ID/name (either course or batch required)', required: false },
				{ name: 'batch_name', type: 'String', desc: 'Batch ID/name', required: false },
				{ name: 'template', type: 'String', desc: 'Certificate template name', required: false },
				{ name: 'issue_date', type: 'String', desc: 'Issue date (YYYY-MM-DD)', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_issue_certificate" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "member=student@example.com" \\
  -d "course=python-basics"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_issue_certificate"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"member": "student@example.com", "course": "python-basics"}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	quizzes: [
		{
			name: 'List Quizzes',
			endpoint: 'lms.lms.api.api_get_quizzes',
			method: 'GET',
			description: 'Get list of quizzes.',
			activeLang: 'cURL',
			params: [
				{ name: 'course', type: 'String', desc: 'Filter by course ID/name', required: false },
				{ name: 'lesson', type: 'String', desc: 'Filter by lesson ID/name', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_quizzes?course=python-basics"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_quizzes"
params = {"course": "python-basics"}

response = requests.get(url, params=params)
print(response.json())`
			}
		},
		{
			name: 'Get Quiz Detail',
			endpoint: 'lms.lms.api.api_get_quiz',
			method: 'GET',
			description: 'Get single quiz with questions and options.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Quiz ID/name', required: true }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_quiz?name=python-quiz-1"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_quiz"
params = {"name": "python-quiz-1"}

response = requests.get(url, params=params)
print(response.json())`
			}
		}
	],
	live_classes: [
		{
			name: 'List Live Classes',
			endpoint: 'lms.lms.api.api_get_live_classes',
			method: 'GET',
			description: 'Get list of live classes.',
			activeLang: 'cURL',
			params: [
				{ name: 'batch_name', type: 'String', desc: 'Filter by batch ID/name', required: false },
				{ name: 'host', type: 'String', desc: 'Filter by host email', required: false },
				{ name: 'date_from', type: 'String', desc: 'Filter classes from this date (YYYY-MM-DD)', required: false },
				{ name: 'date_to', type: 'String', desc: 'Filter classes until this date (YYYY-MM-DD)', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_live_classes?batch_name=batch-2024" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_live_classes"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"batch_name": "batch-2024"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Create Live Class',
			endpoint: 'lms.lms.api.api_create_live_class',
			method: 'POST',
			description: 'Create a new live class. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'title', type: 'String', desc: 'Class title', required: true },
				{ name: 'host', type: 'String', desc: 'Host email', required: true },
				{ name: 'date', type: 'String', desc: 'Date (YYYY-MM-DD)', required: true },
				{ name: 'time', type: 'String', desc: 'Time (HH:MM:SS)', required: true },
				{ name: 'duration', type: 'Integer', desc: 'Duration in minutes', required: true },
				{ name: 'timezone', type: 'String', desc: 'Timezone', required: true },
				{ name: 'meeting_platform', type: 'String', desc: 'Google Meet/Zoom/etc (default: Google Meet)', required: false },
				{ name: 'batch_name', type: 'String', desc: 'Batch ID/name', required: false },
				{ name: 'google_meet_link', type: 'String', desc: 'Google Meet link', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_create_live_class" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "title=Python Intro Session" \\
  -d "host=instructor@example.com" \\
  -d "date=2024-01-15" \\
  -d "time=14:00:00" \\
  -d "duration=60" \\
  -d "timezone=Asia/Jakarta"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_create_live_class"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {
    "title": "Python Intro Session",
    "host": "instructor@example.com",
    "date": "2024-01-15",
    "time": "14:00:00",
    "duration": 60,
    "timezone": "Asia/Jakarta"
}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		},
		{
			name: 'Update Live Class',
			endpoint: 'lms.lms.api.api_update_live_class',
			method: 'POST',
			description: 'Update live class. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Live Class ID - REQUIRED', required: true },
				{ name: 'title', type: 'String', desc: 'Class title', required: false },
				{ name: 'date', type: 'String', desc: 'Date (YYYY-MM-DD)', required: false },
				{ name: 'time', type: 'String', desc: 'Time (HH:MM:SS)', required: false },
				{ name: 'duration', type: 'Integer', desc: 'Duration in minutes', required: false },
				{ name: 'google_meet_link', type: 'String', desc: 'Google Meet link', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_update_live_class" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "name=LC-00001" \\
  -d "duration=90"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_update_live_class"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"name": "LC-00001", "duration": 90}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	commissions: [
		{
			name: 'List Commissions',
			endpoint: 'lms.lms.api.api_get_commissions',
			method: 'GET',
			description: 'Get list of referral commissions. Admin only.',
			activeLang: 'cURL',
			params: [
				{ name: 'referrer', type: 'String', desc: 'Filter by referrer email', required: false },
				{ name: 'payout_status', type: 'String', desc: 'Filter by status (Pending/Processing/Paid)', required: false },
				{ name: 'date_from', type: 'String', desc: 'Filter from this date (YYYY-MM-DD)', required: false },
				{ name: 'date_to', type: 'String', desc: 'Filter until this date (YYYY-MM-DD)', required: false },
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_commissions?payout_status=Pending" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_commissions"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"payout_status": "Pending"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Get Commission Detail',
			endpoint: 'lms.lms.api.api_get_commission',
			method: 'GET',
			description: 'Get single commission detail. Admin only.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Commission ID', required: true }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_commission?name=COM-00001" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_commission"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"name": "COM-00001"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		},
		{
			name: 'Update Commission',
			endpoint: 'lms.lms.api.api_update_commission',
			method: 'POST',
			description: 'Update single commission. Admin only.',
			activeLang: 'cURL',
			params: [
				{ name: 'name', type: 'String', desc: 'Commission ID - REQUIRED', required: true },
				{ name: 'payout_status', type: 'String', desc: 'Payout status (Pending/Processing/Paid)', required: false },
				{ name: 'payout_date', type: 'String', desc: 'Payout date (YYYY-MM-DD)', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_update_commission" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "name=COM-00001" \\
  -d "payout_status=Paid" \\
  -d "payout_date=2024-01-15"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_update_commission"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"name": "COM-00001", "payout_status": "Paid", "payout_date": "2024-01-15"}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		},
		{
			name: 'Bulk Update Commissions',
			endpoint: 'lms.lms.api.api_bulk_update_commissions',
			method: 'POST',
			description: 'Bulk update multiple commission records. Admin only. Great for n8n.',
			activeLang: 'cURL',
			params: [
				{ name: 'commission_ids', type: 'Array/JSON', desc: 'Array of commission IDs to update', required: true },
				{ name: 'payout_status', type: 'String', desc: 'New payout status (Pending/Processing/Paid)', required: false },
				{ name: 'payout_date', type: 'String', desc: 'Payout date (YYYY-MM-DD)', required: false },
				{ name: 'payout_notes', type: 'String', desc: 'Notes about the payout', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_bulk_update_commissions" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d 'commission_ids=["COM-00001","COM-00002"]' \\
  -d "payout_status=Paid" \\
  -d "payout_date=2024-01-15"`,
				Python: `import requests
import json

url = "https://your-site.com/api/method/lms.lms.api.api_bulk_update_commissions"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {
    "commission_ids": json.dumps(["COM-00001", "COM-00002"]),
    "payout_status": "Paid",
    "payout_date": "2024-01-15"
}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	categories: [
		{
			name: 'List Categories',
			endpoint: 'lms.lms.api.api_get_categories',
			method: 'GET',
			description: 'Get list of all categories. Public access.',
			activeLang: 'cURL',
			params: [
				{ name: 'start', type: 'Integer', desc: 'Pagination offset', required: false },
				{ name: 'limit', type: 'Integer', desc: 'Max results (default 100)', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_categories"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_categories"

response = requests.get(url)
print(response.json())`
			}
		},
		{
			name: 'Create Category',
			endpoint: 'lms.lms.api.api_create_category',
			method: 'POST',
			description: 'Create a new category. Admin/Moderator only.',
			activeLang: 'cURL',
			params: [
				{ name: 'category_name', type: 'String', desc: 'Category name - REQUIRED', required: true },
				{ name: 'image', type: 'String', desc: 'Category image URL', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.api_create_category" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "category_name=Data Science"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_create_category"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {"category_name": "Data Science"}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	],
	statistics: [
		{
			name: 'Dashboard Stats',
			endpoint: 'lms.lms.api.api_get_dashboard_stats',
			method: 'GET',
			description: 'Get dashboard statistics. Admin/Moderator only. Returns counts for courses, batches, enrollments, revenue, etc.',
			activeLang: 'cURL',
			params: [],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_dashboard_stats" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_dashboard_stats"
headers = {"Authorization": "token API_KEY:API_SECRET"}

response = requests.get(url, headers=headers)
print(response.json())`
			}
		},
		{
			name: 'Revenue Stats',
			endpoint: 'lms.lms.api.api_get_revenue_stats',
			method: 'GET',
			description: 'Get revenue statistics with date range. Admin only.',
			activeLang: 'cURL',
			params: [
				{ name: 'date_from', type: 'String', desc: 'Start date (YYYY-MM-DD)', required: false },
				{ name: 'date_to', type: 'String', desc: 'End date (YYYY-MM-DD)', required: false },
				{ name: 'group_by', type: 'String', desc: 'Group by: day, week, or month (default: day)', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_revenue_stats?date_from=2024-01-01&date_to=2024-12-31&group_by=month" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_revenue_stats"
headers = {"Authorization": "token API_KEY:API_SECRET"}
params = {"date_from": "2024-01-01", "date_to": "2024-12-31", "group_by": "month"}

response = requests.get(url, headers=headers, params=params)
print(response.json())`
			}
		}
	],
	users: [
		{
			name: 'Get User Profile',
			endpoint: 'lms.lms.api.api_get_user_profile',
			method: 'GET',
			description: 'Get user profile with payout info. Admin can view any user, others can only view self.',
			activeLang: 'cURL',
			params: [
				{ name: 'user_email', type: 'String', desc: 'User email (optional, defaults to current user)', required: false }
			],
			examples: {
				cURL: `curl -X GET "https://your-site.com/api/method/lms.lms.api.api_get_user_profile" \\
  -H "Authorization: token API_KEY:API_SECRET"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.api_get_user_profile"
headers = {"Authorization": "token API_KEY:API_SECRET"}

response = requests.get(url, headers=headers)
print(response.json())`
			}
		},
		{
			name: 'Update Payout Info',
			endpoint: 'lms.lms.api.update_payout_info',
			method: 'POST',
			description: 'Update user payout information.',
			activeLang: 'cURL',
			params: [
				{ name: 'payout_method', type: 'String', desc: 'Payout method (OVO/GoPay/DANA/ShopeePay/Bank Transfer)', required: false },
				{ name: 'payout_phone', type: 'String', desc: 'E-wallet phone number', required: false },
				{ name: 'payout_bank', type: 'String', desc: 'Bank name (for Bank Transfer)', required: false },
				{ name: 'payout_account_number', type: 'String', desc: 'Bank account number', required: false },
				{ name: 'payout_account_name', type: 'String', desc: 'Bank account holder name', required: false }
			],
			examples: {
				cURL: `curl -X POST "https://your-site.com/api/method/lms.lms.api.update_payout_info" \\
  -H "Authorization: token API_KEY:API_SECRET" \\
  -d "payout_method=Bank Transfer" \\
  -d "payout_bank=BCA" \\
  -d "payout_account_number=1234567890" \\
  -d "payout_account_name=John Doe"`,
				Python: `import requests

url = "https://your-site.com/api/method/lms.lms.api.update_payout_info"
headers = {"Authorization": "token API_KEY:API_SECRET"}
data = {
    "payout_method": "Bank Transfer",
    "payout_bank": "BCA",
    "payout_account_number": "1234567890",
    "payout_account_name": "John Doe"
}

response = requests.post(url, headers=headers, data=data)
print(response.json())`
			}
		}
	]
})

const activeSectionInfo = computed(() => {
	const section = sections.find(s => s.id === activeSection.value)
	return {
		...section,
		apis: apis[activeSection.value] || []
	}
})
</script>
