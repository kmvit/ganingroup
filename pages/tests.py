from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import MenuItem, Page


class ProductPageTests(TestCase):
    def test_admin_can_create_product_page(self):
        user = get_user_model().objects.create_superuser(
            username='editor', email='editor@example.com', password='test-password')
        self.client.force_login(user)
        add_url = reverse('admin:core_page_add')
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Адрес страницы продукции')

        response = self.client.post(add_url, {
            'admin_title': 'Новая продукция',
            'product_slug': 'novaya-produkciya',
            'h1': 'Новая продукция',
            'subtitle': 'Краткое описание',
            'body': 'Подробное описание',
            'video_url': 'https://drive.google.com/file/d/abc123/view',
            'seo_title': '', 'seo_description': '',
            'cards-TOTAL_FORMS': '0', 'cards-INITIAL_FORMS': '0',
            'cards-MIN_NUM_FORMS': '0', 'cards-MAX_NUM_FORMS': '1000',
        })
        self.assertEqual(response.status_code, 302)
        page = Page.objects.get(product_slug='novaya-produkciya')
        self.assertEqual(page.get_absolute_url(), '/produkciya/novaya-produkciya/')

    def test_admin_created_page_can_be_linked_from_product_menu(self):
        page = Page.objects.create(
            slug='custom_produkciya_testovyy_product',
            product_slug='testovyy-product',
            admin_title='Тестовый продукт',
            h1='Тестовый продукт',
            body='Описание продукта',
            video_file='pages/video/test.mp4',
            photo='pages/test.jpg',
        )
        products = MenuItem.objects.create(title='Продукция', url_name='produkciya')
        MenuItem.objects.create(title=page.admin_title, parent=products, page=page)

        response = self.client.get(reverse('product_detail', kwargs={'product_slug': page.product_slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Описание продукта')
        self.assertContains(response, '<video class="hero-media hero-media-video" autoplay muted loop playsinline', html=False)
        self.assertContains(response, '/media/pages/video/test.mp4')
        self.assertContains(response, '/media/pages/test.jpg')
        self.assertNotContains(response, '<iframe')
        self.assertContains(response, 'href="/produkciya/testovyy-product/"')

    def test_missing_custom_page_returns_404(self):
        response = self.client.get('/produkciya/net-takoy-stranicy/')
        self.assertEqual(response.status_code, 404)
