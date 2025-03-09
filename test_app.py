import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
import json
from app import app

class TestAddConference(unittest.TestCase):
    
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        # Criar sessão fictícia para simular usuário logado
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 'test-user-id',
                'email': 'admin@test.com',
                'access_token': 'fake-token'
            }

    @patch('app.supabase')
    def test_add_conference_success(self, mock_supabase):
        # Configurar o mock do Supabase para simular sucesso na inserção
        mock_response = MagicMock()
        mock_response.data = [{"id": "test123"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Dados de conferência para teste
        conference_data = {
            'id': 'test123',
            'name': 'ICML',
            'full_name': 'International Conference on Machine Learning',
            'dates': '10-15 July 2024',
            'location': 'Vienna, Austria',
            'categories': 'machine-learning, artificial-intelligence',
            'deadline': '2024-01-30 23:59',
            'website': 'icml2024.org',
            'description': 'A leading international academic conference in machine learning.'
        }
        
        # Fazer a requisição POST para adicionar uma conferência
        response = self.client.post('/admin/conferences/new', 
                                   data=conference_data,
                                   follow_redirects=True)
        
        # Verificar se o status da resposta é 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verificar se o Supabase foi chamado corretamente
        mock_supabase.table.assert_called_once_with('conferences')
        mock_supabase.table().insert.assert_called_once()
        
        # Verificar se a resposta contém a mensagem de sucesso
        self.assertIn(b'Confer\xc3\xaancia adicionada com sucesso!', response.data)

    @patch('app.supabase')
    def test_add_conference_error(self, mock_supabase):
        # Configurar o mock para simular um erro
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception('Erro de teste')
        
        # Dados incompletos para provocar erro
        conference_data = {
            'name': 'ICML',
            'full_name': 'International Conference on Machine Learning',
            # outros campos omitidos propositalmente
        }
        
        # Fazer a requisição POST
        response = self.client.post('/admin/conferences/new', 
                                  data=conference_data,
                                  follow_redirects=True)
        
        # Verificar se a resposta contém a mensagem de erro
        self.assertIn(b'Erro ao adicionar confer\xc3\xaancia: Erro de teste', response.data)

    @patch('app.supabase')
    def test_add_conference_with_auto_id(self, mock_supabase):
        # Configurar o mock do Supabase
        mock_response = MagicMock()
        mock_response.data = [{"id": "auto123"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Dados sem ID (deve ser gerado automaticamente)
        conference_data = {
            'name': 'NeurIPS',
            'full_name': 'Neural Information Processing Systems',
            'dates': '9-15 December 2024',
            'location': 'Vancouver, Canada',
            'categories': 'neural-networks,deep-learning',
            'deadline': '2024-05-17 23:59',
            'website': 'neurips2024.cc',
            'description': 'Leading conference on neural networks and deep learning'
        }
        
        # Fazer a requisição POST
        response = self.client.post('/admin/conferences/new', 
                                  data=conference_data,
                                  follow_redirects=True)
        
        # Verificar se o status da resposta é 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Verificar que o método para inserir no Supabase foi chamado
        mock_supabase.table.assert_called_once_with('conferences')
        mock_supabase.table().insert.assert_called_once()
        
        # Verificamos que um ID foi gerado (não podemos checar o valor exato pois é aleatório)
        call_args = mock_supabase.table().insert.call_args[0][0]
        self.assertIsNotNone(call_args.get('id'))

if __name__ == '__main__':
    unittest.main()
